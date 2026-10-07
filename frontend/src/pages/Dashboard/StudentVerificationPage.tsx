import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Clock3, FileCheck2, XCircle } from "lucide-react";

import {
  getApiErrorMessage,
} from "@/lib/api";
import {
  getMyStudentVerification,
  submitStudentApplication,
  withdrawStudentApplication,
  type StudentApplicationInput,
  type StudentVerificationStatus,
} from "@/services/studentVerification";

const emptyForm = {
  applicant_name: "",
  institution_name: "",
  enrollment_number: "",
  course_or_program: "",
  academic_year: "",
  graduation_year: "",
  institution_email: "",
  additional_information: "",
};

export default function StudentVerificationPage() {
  const [status, setStatus] = useState<StudentVerificationStatus | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [proof, setProof] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [withdrawConfirmOpen, setWithdrawConfirmOpen] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStatus(await getMyStudentVerification());
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "Unable to load your student verification status."
        )
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const application = status?.application;
  const applicationPending = application?.status === "pending";
  const showForm = !applicationPending && !status?.student_access_active;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!proof) {
      setError("Select a PDF, JPEG, or PNG proof document.");
      return;
    }
    if (proof.size > 10 * 1024 * 1024) {
      setError("The proof document must be 10 MB or smaller.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setMessage(null);
    const payload: StudentApplicationInput = {
      ...form,
      graduation_year: form.graduation_year,
      institution_email: form.institution_email,
      additional_information: form.additional_information,
      proof_document: proof,
    };
    try {
      await submitStudentApplication(payload);
      setForm(emptyForm);
      setProof(null);
      setMessage("Application submitted. An admin will review your documents.");
      await refresh();
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "Unable to submit your application.")
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleWithdraw() {
    if (!application) return;
    setWithdrawConfirmOpen(true);
  }

  async function confirmWithdraw() {
    if (!application) return;

    setWithdrawConfirmOpen(false);
    setWithdrawing(true);
    setError(null);
    try {
      await withdrawStudentApplication(application.id);
      setMessage("Your application was withdrawn and the uploaded proof deleted.");
      await refresh();
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "Unable to withdraw your application.")
      );
    } finally {
      setWithdrawing(false);
    }
  }

  return (
    <div className="mx-auto min-w-0 max-w-4xl space-y-6">
      <header>
        <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
          Student Pro Verification
        </h2>
        <p className="mt-2 text-muted-foreground">
          Submit current enrollment information for admin review. Pro access is
          granted only after approval and lasts 365 days.
        </p>
      </header>

      {error && (
        <div role="alert" className="rounded-xl border border-destructive/40 bg-card p-4 text-destructive">
          {error}
          <button
            type="button"
            onClick={() => void refresh()}
            className="ml-3 underline"
          >
            Retry
          </button>
        </div>
      )}
      {message && (
        <p role="status" className="rounded-xl border border-border bg-card p-4 text-foreground">
          {message}
        </p>
      )}

      {loading ? (
        <p role="status" className="text-muted-foreground">
          Loading your verification status...
        </p>
      ) : (
        <>
          {application && (
            <section className="space-y-4 rounded-2xl border border-border bg-card p-5 sm:p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-lg font-semibold text-foreground">
                  Application status
                </h3>
                <span className="rounded-full bg-secondary px-3 py-1 text-sm font-medium capitalize text-secondary-foreground">
                  {status?.student_access_active ? "approved · active" : application.status}
                </span>
              </div>
              <p className="break-words text-sm text-muted-foreground">
                {application.institution_name} · {application.course_or_program}
              </p>
              {application.status === "pending" && (
                <div className="flex items-start gap-3 rounded-xl bg-secondary/60 p-4">
                  <Clock3 className="mt-0.5 size-5 shrink-0 text-primary" />
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">Awaiting review</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Your private proof document is available only to admins.
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={withdrawing}
                    onClick={() => void handleWithdraw()}
                    className="ml-auto shrink-0 text-sm font-medium text-destructive underline disabled:opacity-60"
                  >
                    {withdrawing ? "Withdrawing..." : "Withdraw"}
                  </button>
                </div>
              )}
              {status?.student_access_active && status.student_access_expires_at && (
                <div className="flex items-start gap-3 rounded-xl bg-secondary/60 p-4">
                  <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-primary" />
                  <p className="text-sm text-foreground">
                    Student Pro access is active until{" "}
                    <time dateTime={status.student_access_expires_at}>
                      {new Date(status.student_access_expires_at).toLocaleDateString()}
                    </time>
                    .
                  </p>
                </div>
              )}
              {application.status === "approved" && !status?.student_access_active && (
                <p className="text-sm text-muted-foreground">
                  This application&apos;s student access has expired. You may submit a new application.
                </p>
              )}
              {application.status === "rejected" && (
                <div className="flex items-start gap-3 rounded-xl bg-destructive/5 p-4">
                  <XCircle className="mt-0.5 size-5 shrink-0 text-destructive" />
                  <p className="break-words text-sm text-foreground">
                    {application.rejection_reason || "The application was not approved."}
                  </p>
                </div>
              )}
            </section>
          )}

          {showForm && (
            <form
              onSubmit={(event) => void handleSubmit(event)}
              className="space-y-5 rounded-2xl border border-border bg-card p-5 sm:p-6"
            >
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  {application ? "Submit a new application" : "Apply for student Pro"}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Upload a current enrollment letter, student ID, or other document showing active enrollment.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <label className="space-y-1.5 text-sm font-medium text-foreground">
                  Full name
                  <input required maxLength={100} value={form.applicant_name} onChange={(event) => setForm({ ...form, applicant_name: event.target.value })} className="w-full rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground">
                  Institution
                  <input required maxLength={200} value={form.institution_name} onChange={(event) => setForm({ ...form, institution_name: event.target.value })} className="w-full rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground">
                  Student/enrollment number
                  <input required maxLength={100} value={form.enrollment_number} onChange={(event) => setForm({ ...form, enrollment_number: event.target.value })} className="w-full rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground">
                  Course or program
                  <input required maxLength={200} value={form.course_or_program} onChange={(event) => setForm({ ...form, course_or_program: event.target.value })} className="w-full rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground">
                  Current academic year
                  <input required maxLength={50} value={form.academic_year} onChange={(event) => setForm({ ...form, academic_year: event.target.value })} placeholder="e.g. 2025–2026" className="w-full rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground">
                  Expected graduation year
                  <input required type="number" min={1900} max={2200} value={form.graduation_year} onChange={(event) => setForm({ ...form, graduation_year: event.target.value })} className="w-full rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground sm:col-span-2">
                  Institution email (optional)
                  <input type="email" maxLength={255} value={form.institution_email} onChange={(event) => setForm({ ...form, institution_email: event.target.value })} className="w-full rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground sm:col-span-2">
                  Additional information (optional)
                  <textarea maxLength={1000} rows={3} value={form.additional_information} onChange={(event) => setForm({ ...form, additional_information: event.target.value })} className="w-full resize-y rounded-lg border border-input bg-background px-3 py-2.5" />
                </label>
                <label className="space-y-1.5 text-sm font-medium text-foreground sm:col-span-2">
                  Enrollment proof
                  <span className="block text-xs font-normal text-muted-foreground">
                    PDF, JPEG, or PNG · maximum 10 MB. Documents are private and accessible only to admins.
                  </span>
                  <input
                    required
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                    onChange={(event) => setProof(event.target.files?.[0] ?? null)}
                    className="block w-full min-w-0 rounded-lg border border-input bg-background p-2 text-sm text-foreground file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-2 file:text-secondary-foreground"
                  />
                  {proof && (
                    <span className="flex items-center gap-2 break-all text-xs text-muted-foreground">
                      <FileCheck2 className="size-4 shrink-0" />
                      {proof.name}
                    </span>
                  )}
                </label>
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
              >
                {submitting ? "Submitting..." : "Submit for review"}
              </button>
            </form>
          )}
        </>
      )}

      {withdrawConfirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !withdrawing) {
              setWithdrawConfirmOpen(false);
            }
          }}
        >
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="withdraw-confirm-title"
            aria-describedby="withdraw-confirm-description"
            className="w-full max-w-md rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl"
          >
            <h2 id="withdraw-confirm-title" className="text-lg font-semibold">
              Withdraw application?
            </h2>
            <p id="withdraw-confirm-description" className="mt-2 text-sm text-muted-foreground">
              Withdraw this pending application? Your uploaded proof document will also be deleted.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                disabled={withdrawing}
                onClick={() => setWithdrawConfirmOpen(false)}
                className="rounded-lg border border-border bg-background px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={withdrawing}
                onClick={() => void confirmWithdraw()}
                className="rounded-lg bg-destructive px-4 py-2.5 text-sm font-semibold text-destructive-foreground transition-colors hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive disabled:cursor-not-allowed disabled:opacity-50"
              >
                {withdrawing ? "Withdrawing..." : "Withdraw"}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
