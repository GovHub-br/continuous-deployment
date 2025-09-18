import os
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SUP_URL      = os.getenv("SUP_URL", "https://superset.lappis.ipea.gov.br").rstrip("/")
SUP_USERNAME = os.getenv("SUP_USERNAME", "admin")
SUP_PASSWORD = os.getenv("SUP_PASSWORD", "")
VERIFY_TLS   = os.getenv("VERIFY_TLS", "true").lower() not in ("0", "false", "no")

app = FastAPI(title="Superset Guest Token Issuer (mini, no-default)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

class TokenOut(BaseModel):
    token: str

async def _login(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{SUP_URL}/api/v1/security/login",
        headers={"Content-Type": "application/json"},
        json={"username": SUP_USERNAME, "password": SUP_PASSWORD, "provider": "db", "refresh": True},
    )
    if r.status_code != 200:
        raise HTTPException(502, f"login falhou: {r.text}")
    tok = r.json().get("access_token")
    if not tok:
        raise HTTPException(502, "login sem access_token")
    return tok

async def _csrf(client: httpx.AsyncClient, access_token: str) -> str:
    r = await client.get(
        f"{SUP_URL}/api/v1/security/csrf_token/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if r.status_code != 200:
        raise HTTPException(502, f"csrf_token falhou: {r.text}")
    csrf = r.json().get("result")
    if not csrf:
        raise HTTPException(502, "csrf_token ausente")
    return csrf

async def _guest_token(client: httpx.AsyncClient, access_token: str, csrf: str, dash_uuid: str, username="viewer-app") -> str:
    r = await client.post(
        f"{SUP_URL}/api/v1/security/guest_token/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-CSRFToken": csrf,
            "Referer": SUP_URL,
            "Content-Type": "application/json",
        },
        json={
            "resources": [{"type": "dashboard", "id": dash_uuid}],
            "rls": [],
            "user": {"username": username},
        },
    )
    if r.status_code != 200:
        raise HTTPException(502, f"guest_token falhou: {r.text}")
    tok = r.json().get("token")
    if not tok:
        raise HTTPException(502, "guest token ausente na resposta")
    return tok

@app.get("/guest-token", response_model=TokenOut)
@app.get("/embed/guest-token", response_model=TokenOut)
async def guest_token(
    dash: str = Query(..., description="UUID do dashboard (obrigatório)"),
    username: str = Query("viewer-app", description="Nome lógico do usuário no token"),
):
    async with httpx.AsyncClient(verify=VERIFY_TLS, timeout=20.0) as client:
        access = await _login(client)
        csrf = await _csrf(client, access)
        token = await _guest_token(client, access, csrf, dash, username=username)
        return {"token": token}

@app.get("/health")
async def health():
    return {"ok": True}
