from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import shutil
from pathlib import Path

from app.api.dependencies import get_current_user
from app.core.security import verify_password, hash_password
from app.crud.crud_user import (
    delete_user,
    update_password,
    update_user,
    get_user_by_email,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    UserResponse,
    UserUpdate,
)

router = APIRouter()

# Configuration for profile pictures
PROFILE_PICTURES_DIR = Path("app/uploads/profile_pictures")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure directory exists
PROFILE_PICTURES_DIR.mkdir(parents=True, exist_ok=True)


# ==========================
# Get Current User
# ==========================

@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


# ==========================
# Update Profile
# ==========================

@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_user = (
        db.query(User)
        .filter(
            User.email == user_data.email,
            User.id != current_user.id,
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    return update_user(
        db=db,
        user=current_user,
        full_name=user_data.full_name,
        email=user_data.email,
    )


# ==========================
# Upload Profile Picture
# ==========================

@router.post(
    "/me/profile-picture",
    response_model=UserResponse,
)
def upload_profile_picture(
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a profile picture for the current user.
    Supported formats: JPG, JPEG, PNG, WEBP
    Maximum size: 5MB
    """
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided.",
        )

    # Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content to check size
    try:
        file_content = file.file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file provided.",
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading file: {str(e)}",
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = PROFILE_PICTURES_DIR / unique_filename

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    # Construct URL path
    profile_picture_url = f"/api/v1/users/profile-pictures/{unique_filename}"

    # Update user in database
    current_user.profile_picture = profile_picture_url
    db.commit()
    db.refresh(current_user)

    return current_user


# ==========================
# Serve Profile Pictures
# ==========================

@router.get("/profile-pictures/{filename}")
async def serve_profile_picture(filename: str):
    """
    Serve profile picture files.
    """
    # Security: prevent path traversal
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    file_path = PROFILE_PICTURES_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found.",
        )

    from fastapi.responses import FileResponse
    
    return FileResponse(
        file_path,
        media_type="image/jpeg" if filename.endswith((".jpg", ".jpeg")) else 
                   "image/png" if filename.endswith(".png") else
                   "image/webp",
    )


# ==========================
# Set Built-in Avatar
# ==========================

@router.post(
    "/me/avatar",
    response_model=UserResponse,
)
def set_builtin_avatar(
    avatar_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set a built-in avatar for the current user.
    Avatar IDs: avatar_01 through avatar_08
    """
    valid_avatars = [f"avatar_{i:02d}" for i in range(1, 9)]
    
    if avatar_id not in valid_avatars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid avatar ID. Choose from: {', '.join(valid_avatars)}",
        )

    # Store avatar identifier (frontend will resolve to actual image)
    current_user.profile_picture = f"builtin:{avatar_id}"
    db.commit()
    db.refresh(current_user)

    return current_user


# ==========================
# Remove Profile Picture
# ==========================

@router.delete(
    "/me/profile-picture",
    response_model=UserResponse,
)
def remove_profile_picture(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove the current user's profile picture.
    """
    # If it's a custom uploaded picture, delete the file
    if current_user.profile_picture and not current_user.profile_picture.startswith("builtin:"):
        # Extract filename from URL
        filename = current_user.profile_picture.split("/")[-1]
        file_path = PROFILE_PICTURES_DIR / filename
        
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignore file deletion errors

    current_user.profile_picture = None
    db.commit()
    db.refresh(current_user)

    return current_user


# ==========================
# Change Password
# ==========================

@router.post(
    "/me/change-password",
)
def change_current_user_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(
        password_data.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if (
        password_data.current_password
        == password_data.new_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password.",
        )

    update_password(
        db=db,
        user=current_user,
        new_password=password_data.new_password,
    )

    return {
        "message": "Password changed successfully.",
    }


# ==========================
# Delete Account
# ==========================

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Delete custom profile picture if exists
    if current_user.profile_picture and not current_user.profile_picture.startswith("builtin:"):
        filename = current_user.profile_picture.split("/")[-1]
        file_path = PROFILE_PICTURES_DIR / filename
        
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass

    delete_user(
        db=db,
        user=current_user,
    )

    return None