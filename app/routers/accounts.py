from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/accounts", tags=["accounts"])


def get_account_or_404(db: Session, account_id: int) -> models.Account:
    account = db.get(models.Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("", response_model=schemas.AccountOut, status_code=201)
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)):
    account = models.Account(owner_name=payload.owner_name, balance=0)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=schemas.AccountOut)
def read_account(account_id: int, db: Session = Depends(get_db)):
    return get_account_or_404(db, account_id)
