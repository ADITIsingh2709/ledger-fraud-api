from fastapi import FastAPI

from app import models  # noqa: F401  (registers the tables)
from app.database import Base, engine
from app.routers import accounts, flags, transactions, transfers

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ledger & Fraud Flagging API")
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(transfers.router)
app.include_router(flags.router)


@app.get("/health")
def health():
    return {"status": "ok"}
