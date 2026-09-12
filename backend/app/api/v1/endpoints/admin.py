from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.api.dependencies import get_current_admin_user
from app.models.user import User
from app.models.dataset import Dataset
from app.schemas.admin import AdminDashboardStats, AdminUserResponse, AdminDatasetResponse, SystemHealthSchema
from app.services.admin_service import AdminService

router = APIRouter()

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    return AdminService.get_dashboard_stats(db)

@router.get("/system-health", response_model=SystemHealthSchema)
def get_system_health(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    return AdminService.get_system_health(db)

@router.get("/users", response_model=List[AdminUserResponse])
def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    users = db.query(User).all()
    result = []
    for u in users:
        d_count = db.query(Dataset).filter(Dataset.user_id == u.id).count()
        result.append(AdminUserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            created_at=u.created_at,
            dataset_count=d_count
        ))
    return result

@router.patch("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot alter your own admin status")
    
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User status updated to {'active' if user.is_active else 'inactive'}"}

@router.get("/datasets", response_model=List[AdminDatasetResponse])
def list_all_datasets(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    datasets = db.query(Dataset).all()
    res = []
    for d in datasets:
        owner = db.query(User).filter(User.id == d.user_id).first()
        res.append(AdminDatasetResponse(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            row_count=d.row_count,
            column_count=d.column_count,
            file_size_bytes=d.file_size_bytes,
            quality_score=d.analysis.quality_score if d.analysis else None,
            created_at=d.created_at,
            owner_email=owner.email if owner else "Unknown"
        ))
    return res

@router.delete("/datasets/{dataset_id}")
def admin_delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(dataset)
    db.commit()
    return {"message": "Dataset purged successfully by admin"}