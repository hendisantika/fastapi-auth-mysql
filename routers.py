from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from security import get_current_user

SORTABLE_FIELDS = {"id", "name", "price", "created_at", "updated_at"}

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/", response_model=schemas.ItemResponse)
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_item = models.Item(
        name=item.name,
        price=item.price,
        created_by=current_user.username,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=schemas.PaginatedItems)
def get_items(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    name: str | None = Query(None, description="Filter by name (partial match)"),
    min_price: float | None = Query(None, ge=0, description="Minimum price"),
    max_price: float | None = Query(None, ge=0, description="Maximum price"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction"),
):
    if sort_by not in SORTABLE_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Allowed: {sorted(SORTABLE_FIELDS)}",
        )

    query = db.query(models.Item)

    if name:
        query = query.filter(models.Item.name.ilike(f"%{name}%"))
    if min_price is not None:
        query = query.filter(models.Item.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Item.price <= max_price)

    total = query.count()

    sort_column = getattr(models.Item, sort_by)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))

    items = query.offset(skip).limit(limit).all()
    return schemas.PaginatedItems(total=total, skip=skip, limit=limit, items=items)


@router.get("/{item_id}", response_model=schemas.ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int,
    updated_item: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    item.name = updated_item.name
    item.price = updated_item.price
    item.updated_by = current_user.username
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}
