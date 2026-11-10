from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.accounts import get_account_or_404
from app.services import fraud_rules

router = APIRouter(prefix="/accounts", tags=["transactions"])


@router.post("/{account_id}/deposit", response_model=schemas.TransactionOut, status_code=201)
def deposit(account_id: int, payload: schemas.AmountIn, db: Session = Depends(get_db)):
    account = get_account_or_404(db, account_id)
    account.balance = account.balance + payload.amount
    txn = models.Transaction(type="deposit", amount=payload.amount, to_account_id=account.id)
    db.add(txn)
    db.flush()  # assigns txn.id so the rules can look at it
    fraud_rules.evaluate(db, txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.post("/{account_id}/withdraw", response_model=schemas.TransactionOut, status_code=201)
def withdraw(account_id: int, payload: schemas.AmountIn, db: Session = Depends(get_db)):
    account = get_account_or_404(db, account_id)
    if account.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    account.balance = account.balance - payload.amount
    txn = models.Transaction(type="withdrawal", amount=payload.amount, from_account_id=account.id)
    db.add(txn)
    db.flush()
    fraud_rules.evaluate(db, txn)
    db.commit()
    db.refresh(txn)
    return txn
