# app/main.py

from fastapi import FastAPI, Depends, HTTPException, Request
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.db import engine
from app.models import Base
from app.api import attendance

# create app
app = FastAPI(title="CheckInMate")
# set router
app.include_router(attendance.router)


#static, template
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")


ALLOWED_IPS = {"127.0.0.1", "192.168.35.7", "210.124.110.147"}

def get_real_ip(request: Request) -> str:
    # 1) Cloudflare가 보장하는 원본 IP
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    # 2) 일반 프록시 체인: 첫 번째가 원본
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()

    # 3) 마지막 fallback (직접 접속 or 내부)
    return request.client.host

def ip_guard(request: Request):
    client_ip = get_real_ip(request)
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail=f"Access denied: {client_ip}")

# ============ Allowed Pages ==============

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    context = {"request": request, "title": "CheckInMate"}
    return templates.TemplateResponse("external_log.html", context)

@app.get("/room", response_class=HTMLResponse)
async def room(request: Request):
    context = {"request": request, "title": "재실 인원 조회"}
    return templates.TemplateResponse("external_activated.html", context)


# ============ Blocked Pages =================

@app.get("/logview", response_class=HTMLResponse, dependencies=[Depends(ip_guard)])
async def logView(request: Request, id: int):
    context = {"request": request, "title": "CheckInMate-Log", "id": id}
    return templates.TemplateResponse("kiosk_log.html", context)

@app.get("/kiosk", response_class=HTMLResponse, dependencies=[Depends(ip_guard)])
async def kiosk(request: Request):
    context = {"request": request, "title": "CheckInMate"}
    return templates.TemplateResponse("kiosk_main.html", context)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# =========== For Debug ==================
@app.get("/debug/ip")
def debug_ip(request: Request):
    return {
        "client": request.client.host,
        "x_real_ip": request.headers.get("x-real-ip"),
        "x_forwarded_for": request.headers.get("x-forwarded-for"),
        "cf_connecting_ip": request.headers.get("cf-connecting-ip"),
    }