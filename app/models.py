from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("balance >= 0", name="ck_balance_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_name: Mapped[str] = mapped_column(String(100))
    balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(20))  # deposit, withdrawal, transfer
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    from_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    to_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"))
    rule: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
