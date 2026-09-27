from __future__ import annotations
import json
import urllib.parse
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from config.settings import settings
from database.engine import get_db
from database.models import OAuthCredential, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timezone, timedelta

router=APIRouter(prefix="/auth", tags=["auth"])
FRONTEND=settings.FRONTEND_URL

def _finish_session(name:str,email:str,provider:str):
    payload={"name":name or email.split('@')[0] or "User","email":email,"guest":False,"provider":provider}
    js=json.dumps(payload)
    return HTMLResponse(f'''<!doctype html><html><body><script>localStorage.setItem("a2z-nexus-session", {json.dumps(js)});window.location.replace({(FRONTEND+'/chat')!r});</script><p>Signing you in…</p></body></html>''')

@router.get("/google")
async def google_login():
    if not settings.GOOGLE_CLIENT_ID: raise HTTPException(503,"Google OAuth is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    q=urllib.parse.urlencode({"client_id":settings.GOOGLE_CLIENT_ID,"redirect_uri":settings.GOOGLE_REDIRECT_URI,"response_type":"code","scope":"openid email profile https://www.googleapis.com/auth/calendar.events","access_type":"offline","prompt":"select_account"})
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?"+q)

@router.get("/google/callback")
async def google_callback(code:str, db: AsyncSession = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET: raise HTTPException(503,"Google OAuth is not configured.")
    async with httpx.AsyncClient(timeout=30) as client:
        token=await client.post("https://oauth2.googleapis.com/token",data={"code":code,"client_id":settings.GOOGLE_CLIENT_ID,"client_secret":settings.GOOGLE_CLIENT_SECRET,"redirect_uri":settings.GOOGLE_REDIRECT_URI,"grant_type":"authorization_code"})
        token.raise_for_status(); token_data=token.json(); access=token_data.get("access_token")
        info=await client.get("https://openidconnect.googleapis.com/v1/userinfo",headers={"Authorization":f"Bearer {access}"})
        info.raise_for_status(); u=info.json()
    email=u.get("email","")
    result=await db.execute(select(User).where(User.email==email))
    user=result.scalar_one_or_none()
    if user is None:
        user=User(id=str(uuid.uuid4()), name=u.get("name","") or email.split("@")[0], email=email)
        db.add(user); await db.commit(); await db.refresh(user)
    result=await db.execute(select(OAuthCredential).where(OAuthCredential.user_id==user.id, OAuthCredential.provider=="google"))
    cred=result.scalar_one_or_none()
    expires=token_data.get("expires_in")
    if cred is None:
        cred=OAuthCredential(id=str(uuid.uuid4()), user_id=user.id, provider="google", access_token=access or "", refresh_token=token_data.get("refresh_token"), expires_at=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=int(expires)) if expires else None)
        db.add(cred)
    else:
        cred.access_token=access or cred.access_token
        if token_data.get("refresh_token"): cred.refresh_token=token_data["refresh_token"]
        if expires: cred.expires_at=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=int(expires))
    await db.commit()
    return _finish_session(u.get("name",""),email,"google")

@router.get("/microsoft")
async def microsoft_login():
    if not settings.MICROSOFT_CLIENT_ID: raise HTTPException(503,"Microsoft OAuth is not configured. Add MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET.")
    tenant=settings.MICROSOFT_TENANT_ID or "common"
    q=urllib.parse.urlencode({"client_id":settings.MICROSOFT_CLIENT_ID,"response_type":"code","redirect_uri":settings.MICROSOFT_REDIRECT_URI,"response_mode":"query","scope":"openid profile email User.Read"})
    return RedirectResponse(f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?"+q)

@router.get("/microsoft/callback")
async def microsoft_callback(code:str, db: AsyncSession = Depends(get_db)):
    if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET: raise HTTPException(503,"Microsoft OAuth is not configured.")
    tenant=settings.MICROSOFT_TENANT_ID or "common"
    async with httpx.AsyncClient(timeout=30) as client:
        token=await client.post(f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",data={"client_id":settings.MICROSOFT_CLIENT_ID,"client_secret":settings.MICROSOFT_CLIENT_SECRET,"code":code,"redirect_uri":settings.MICROSOFT_REDIRECT_URI,"grant_type":"authorization_code","scope":"openid profile email User.Read"})
        token.raise_for_status(); access=token.json().get("access_token")
        info=await client.get("https://graph.microsoft.com/v1.0/me",headers={"Authorization":f"Bearer {access}"})
        info.raise_for_status(); u=info.json()
    email = (u.get("mail") or u.get("userPrincipalName") or "").strip().lower()
    name = u.get("displayName","") or email.split("@")[0] or "User"
    if not email:
        raise HTTPException(400, "Microsoft account did not provide an email address.")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=str(uuid.uuid4()), name=name, email=email)
        db.add(user)
        await db.commit()
    return _finish_session(name, email, "microsoft")
