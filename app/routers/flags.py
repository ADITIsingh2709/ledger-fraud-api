from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/flags", tags=["flags"])


@router.get("", response_model=list[schemas.FlagOut])
def list_flags(status: str | None = None, db: Session = Depends(get_db)):
    """List flagged transactions, newest first. Filter with ?status=pending."""
    query = select(models.Flag).order_by(models.Flag.id.desc())
    if status:
        query = query.where(models.Flag.status == status)
    return db.scalars(query).all()


@router.patch("/{flag_id}", response_model=schemas.FlagOut)
def review_flag(flag_id: int, payload: schemas.FlagReview, db: Session = Depends(get_db)):
    """Mark a flag as reviewed or dismissed."""
    flag = db.get(models.Flag, flag_id)
    if flag is None:
        raise HTTPException(status_code=404, detail="Flag not found")
    flag.status = payload.status
    db.commit()
    db.refresh(flag)
    return flag
