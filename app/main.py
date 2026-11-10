from fastapi import FastAPI

app = FastAPI(title="Ledger & Fraud Flagging API")


@app.get("/health")
def health():
    return {"status": "ok"}
