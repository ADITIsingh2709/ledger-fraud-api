from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.accounts import get_account_or_404

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=schemas.TransactionOut, status_code=201)
def transfer(payload: schemas.TransferIn, db: Session = Depends(get_db)):
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    source = get_account_or_404(db, payload.from_account_id)
    destination = get_account_or_404(db, payload.to_account_id)

    if source.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Debit, credit and the ledger entry are saved in ONE database transaction:
    # either all three succeed or none of them do.
    try:
        source.balance = source.balance - payload.amount
        destination.balance = destination.balance + payload.amount
        txn = models.Transaction(
            type="transfer",
            amount=payload.amount,
            from_account_id=source.id,
            to_account_id=destination.id,
        )
        db.add(txn)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(txn)
    return txn
