from datetime import UTC, datetime, timedelta

from app.models.notification import Notification
from app.models.student_verification import (
    StudentVerificationApplication,
    StudentVerificationStatus,
)
from app.models.subscription import PlanType, Subscription, SubscriptionStatus
from app.models.user import User
from app.services.entitlements import resolve_plan

API = "/api/v1"
PDF = b"%PDF-1.7\nstudent enrollment proof"


def application_payload(
    *, filename="proof.pdf", content=PDF, content_type="application/pdf"
):
    return {
        "data": {
            "applicant_name": "Alice Student",
            "institution_name": "Example University",
            "enrollment_number": "STU-1004",
            "course_or_program": "Data Science",
            "academic_year": "2025-2026",
            "graduation_year": "2027",
            "institution_email": "alice@example.edu",
            "additional_information": "Currently enrolled full time.",
        },
        "files": {
            "proof_document": (filename, content, content_type),
        },
    }


def submit_application(client, auth_headers):
    return client.post(
        f"{API}/student-verification/applications",
        headers=auth_headers,
        **application_payload(),
    )


def test_application_is_private_and_pending_until_admin_approval(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "app.services.student_verification.settings.STUDENT_VERIFICATION_STORAGE_DIR",
        str(tmp_path),
    )
    response = submit_application(client, auth_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert body["proof_available"] is True
    assert "enrollment_number" not in body
    assert "proof_stored_filename" not in body
    assert resolve_plan(db, db.query(User).filter_by(email=user_dict["email"]).one().id)[0] == "free"
    assert len(list(tmp_path.iterdir())) == 1

    duplicate = submit_application(client, auth_headers)
    assert duplicate.status_code == 409

    status_response = client.get(
        f"{API}/student-verification/me",
        headers=auth_headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["application"]["status"] == "pending"


def test_only_admin_can_retrieve_proof_and_approve_once(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "app.services.student_verification.settings.STUDENT_VERIFICATION_STORAGE_DIR",
        str(tmp_path),
    )
    submitted = submit_application(client, auth_headers)
    assert submitted.status_code == 201, submitted.text
    application_id = submitted.json()["id"]

    proof_url = f"{API}/admin/student-verifications/{application_id}/proof"
    assert client.get(proof_url, headers=auth_headers).status_code == 403
    assert (
        client.post(
            f"{API}/admin/student-verifications/{application_id}/approve",
            headers=auth_headers,
        ).status_code
        == 403
    )

    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()

    proof_response = client.get(proof_url, headers=auth_headers)
    assert proof_response.status_code == 200
    assert proof_response.content == PDF
    assert "no-store" in proof_response.headers["cache-control"]

    approve_url = f"{API}/admin/student-verifications/{application_id}/approve"
    approved = client.post(approve_url, headers=auth_headers)
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    expires_at = datetime.fromisoformat(
        approved.json()["student_entitlement_expires_at"]
    )
    reviewed_at = datetime.fromisoformat(approved.json()["admin_reviewed_at"])
    assert expires_at == reviewed_at + timedelta(days=365)
    assert resolve_plan(db, user.id)[0] == "pro"

    notifications_before = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .count()
    )
    repeat = client.post(approve_url, headers=auth_headers)
    assert repeat.status_code == 200
    assert (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .count()
        == notifications_before
    )


def test_paid_business_and_student_entitlement_expiry_precedence(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "app.services.student_verification.settings.STUDENT_VERIFICATION_STORAGE_DIR",
        str(tmp_path),
    )
    submitted = submit_application(client, auth_headers)
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()
    approved = client.post(
        f"{API}/admin/student-verifications/{submitted.json()['id']}/approve",
        headers=auth_headers,
    )
    assert approved.status_code == 200, approved.text
    application = db.get(StudentVerificationApplication, submitted.json()["id"])
    assert resolve_plan(db, user.id)[0] == "pro"

    subscription = Subscription(
        user_id=user.id,
        plan=PlanType.BUSINESS,
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(subscription)
    db.commit()
    assert resolve_plan(db, user.id)[0] == "business"

    subscription.status = SubscriptionStatus.PAST_DUE
    application.student_entitlement_expires_at = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    )
    db.commit()
    assert resolve_plan(db, user.id)[0] == "free"


def test_student_expiry_notifications_are_generated_once(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "app.services.student_verification.settings.STUDENT_VERIFICATION_STORAGE_DIR",
        str(tmp_path),
    )
    submitted = submit_application(client, auth_headers)
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()
    application = db.get(StudentVerificationApplication, submitted.json()["id"])
    application.status = StudentVerificationStatus.APPROVED
    application.student_entitlement_expires_at = (
        datetime.now(UTC).replace(tzinfo=None) + timedelta(days=10)
    )
    db.commit()

    status_url = f"{API}/student-verification/me"
    assert client.get(status_url, headers=auth_headers).status_code == 200
    assert client.get(status_url, headers=auth_headers).status_code == 200
    assert (
        db.query(Notification)
        .filter(
            Notification.user_id == user.id,
            Notification.title == "Student Pro access expires soon",
        )
        .count()
        == 1
    )

    application.student_entitlement_expires_at = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    )
    db.commit()
    expired = client.get(status_url, headers=auth_headers)
    assert expired.status_code == 200
    assert expired.json()["student_access_active"] is False
    assert expired.json()["effective_plan"] == "free"
    assert (
        db.query(Notification)
        .filter(
            Notification.user_id == user.id,
            Notification.title == "Student Pro access expired",
        )
        .count()
        == 1
    )


def test_reviewed_proof_is_deleted_when_retention_expires(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "app.services.student_verification.settings.STUDENT_VERIFICATION_STORAGE_DIR",
        str(tmp_path),
    )
    submitted = submit_application(client, auth_headers)
    application_id = submitted.json()["id"]
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()
    approved = client.post(
        f"{API}/admin/student-verifications/{application_id}/approve",
        headers=auth_headers,
    )
    assert approved.status_code == 200, approved.text
    application = db.get(StudentVerificationApplication, application_id)
    application.proof_delete_after = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    )
    db.commit()

    queue = client.get(
        f"{API}/admin/student-verifications",
        headers=auth_headers,
    )
    assert queue.status_code == 200
    assert list(tmp_path.iterdir()) == []
    assert application.proof_stored_filename is None
    assert (
        client.get(
            f"{API}/admin/student-verifications/{application_id}/proof",
            headers=auth_headers,
        ).status_code
        == 404
    )


def test_rejection_reason_allows_resubmission_and_withdrawal_deletes_proof(
    client, auth_headers, user_dict, db, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "app.services.student_verification.settings.STUDENT_VERIFICATION_STORAGE_DIR",
        str(tmp_path),
    )
    submitted = submit_application(client, auth_headers)
    user = db.query(User).filter_by(email=user_dict["email"]).one()
    user.is_superuser = True
    db.commit()
    rejected = client.post(
        f"{API}/admin/student-verifications/{submitted.json()['id']}/reject",
        headers=auth_headers,
        json={"rejection_reason": "Please provide current enrollment proof."},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["rejection_reason"] == "Please provide current enrollment proof."

    resubmitted = submit_application(client, auth_headers)
    assert resubmitted.status_code == 201, resubmitted.text
    application_id = resubmitted.json()["id"]
    assert len(list(tmp_path.iterdir())) == 2

    withdrawn = client.post(
        f"{API}/student-verification/applications/{application_id}/withdraw",
        headers=auth_headers,
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "withdrawn"
    assert withdrawn.json()["proof_available"] is False
    assert len(list(tmp_path.iterdir())) == 1


def test_proof_requires_matching_safe_document_type(
    client, auth_headers, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "app.services.student_verification.settings.STUDENT_VERIFICATION_STORAGE_DIR",
        str(tmp_path),
    )
    bad_signature = client.post(
        f"{API}/student-verification/applications",
        headers=auth_headers,
        **application_payload(content=b"not actually a PDF"),
    )
    assert bad_signature.status_code == 415
    assert list(tmp_path.iterdir()) == []

    unsupported = client.post(
        f"{API}/student-verification/applications",
        headers=auth_headers,
        **application_payload(filename="../proof.exe", content_type="application/pdf"),
    )
    assert unsupported.status_code == 415
    assert list(tmp_path.iterdir()) == []
