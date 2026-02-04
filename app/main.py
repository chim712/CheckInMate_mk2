# app/main.py

from fastapi import FastAPI, Depends, HTTPException
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.db.db import engine
from app.models import Base
from app.api import attendance
from app.api import admin

# create app
app = FastAPI(title="CheckInMate")
# set router
app.include_router(attendance.router)
app.include_router(admin.router)


#static, template
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")


ALLOWED_IPS = {"127.0.0.1", "192.168.35.7", "192.168.35.80", "210.124.110.147", "220.69.207.5"}

def ip_guard(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="Access denied")

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
    context = {"request": request, "title": "CheckInMate Log", "id": id}
    return templates.TemplateResponse("kiosk_log_800.html", context)

@app.get("/kiosk", response_class=HTMLResponse, dependencies=[Depends(ip_guard)])
async def kiosk(request: Request):
    context = {"request": request, "title": "CheckInMate Kiosk"}
    return templates.TemplateResponse("kiosk_main.html", context)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    context = {"request": request, "title": "Admin Log Page", "orgId": 1}
    return templates.TemplateResponse("admin_log.html", context)