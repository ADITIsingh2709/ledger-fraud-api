from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import models

# All thresholds live here so they are easy to explain and change.
LARGE_AMOUNT_THRESHOLD = Decimal("10000")
VELOCITY_MAX_TXNS = 5
VELOCITY_WINDOW_MINUTES = 10
UNUSUAL_MULTIPLIER = 5
UNUSUAL_MIN_HISTORY = 3


def _actor_account_id(txn: models.Transaction) -> int:
    """The account the transaction belongs to: the sender, or the receiver for deposits."""
    return txn.from_account_id if txn.from_account_id is not None else txn.to_account_id


def _large_amount(txn):
    if txn.amount >= LARGE_AMOUNT_THRESHOLD:
        return "LARGE_AMOUNT", f"Amount {txn.amount} is at or above the {LARGE_AMOUNT_THRESHOLD} threshold"
    return None


def _high_velocity(db: Session, txn):
    account_id = _actor_account_id(txn)
    since = models.utcnow() - timedelta(minutes=VELOCITY_WINDOW_MINUTES)
    count = db.scalar(
        select(func.count())
        .select_from(models.Transaction)
        .where(
            or_(
                models.Transaction.from_account_id == account_id,
                models.Transaction.to_account_id == account_id,
            ),
            models.Transaction.created_at >= since,
        )
    )
    if count > VELOCITY_MAX_TXNS:
        return (
            "HIGH_VELOCITY",
            f"{count} transactions on account {account_id} in the last "
            f"{VELOCITY_WINDOW_MINUTES} minutes (limit {VELOCITY_MAX_TXNS})",
        )
    return None


def _unusual_withdrawal(db: Session, txn):
    if txn.from_account_id is None:  # deposits are not outgoing money
        return None
    previous = db.scalars(
        select(models.Transaction.amount).where(
            models.Transaction.from_account_id == txn.from_account_id,
            models.Transaction.id != txn.id,
        )
    ).all()
    if len(previous) < UNUSUAL_MIN_HISTORY:
        return None
    average = sum(Decimal(str(a)) for a in previous) / len(previous)
    if txn.amount > average * UNUSUAL_MULTIPLIER:
        return (
            "UNUSUAL_WITHDRAWAL",
            f"Amount {txn.amount} is more than {UNUSUAL_MULTIPLIER}x the account's "
            f"average outgoing amount ({average:.2f})",
        )
    return None


def evaluate(db: Session, txn: models.Transaction) -> list[models.Flag]:
    """Run every rule on a transaction (already flushed) and add a Flag for each hit.

    The caller commits, so the transaction and its flags are saved together.
    """
    hits = [
        _large_amount(txn),
        _high_velocity(db, txn),
        _unusual_withdrawal(db, txn),
    ]
    flags = []
    for hit in hits:
        if hit is None:
            continue
        rule, reason = hit
        flag = models.Flag(transaction_id=txn.id, rule=rule, reason=reason)
        db.add(flag)
        flags.append(flag)
    return flags
