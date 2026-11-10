from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    owner_name: str = Field(min_length=1, max_length=100)


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_name: str
    balance: Decimal


class AmountIn(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount: Decimal
    from_account_id: int | None
    to_account_id: int | None


class TransferIn(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
