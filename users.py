from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import require_admin

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_admin)],
)

SORTABLE_FIELDS = {"id", "username", "email", "created_at"}


@router.get("/", response_model=schemas.PaginatedUsers)
def get_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    username: str | None = Query(None, description="Filter by username (partial)"),
    email: str | None = Query(None, description="Filter by email (partial)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction"),
):
    if sort_by not in SORTABLE_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Allowed: {sorted(SORTABLE_FIELDS)}",
        )

    query = db.query(models.User)

    if username:
        query = query.filter(models.User.username.ilike(f"%{username}%"))
    if email:
        query = query.filter(models.User.email.ilike(f"%{email}%"))
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)

    total = query.count()

    sort_column = getattr(models.User, sort_by)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))

    users = query.offset(skip).limit(limit).all()
    return schemas.PaginatedUsers(total=total, skip=skip, limit=limit, users=users)


@router.patch("/{user_id}/role", response_model=schemas.UserResponse)
def update_user_role(
    user_id: int,
    payload: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id and payload.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Admins cannot revoke their own admin role",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Admins cannot delete their own account",
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
