# app/main.py

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.api import attendance

# create app
app = FastAPI(title="CheckInMate")
# set router
app.include_router(attendance.router)


#static, template
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    context = {"request": request, "title": "CheckInMate"}
    return templates.TemplateResponse("kiosk_main.html", context)

@app.get("/logview", response_class=HTMLResponse)
async def logView(request: Request, id: int):
    context = {"request": request, "title": "CheckInMate-Log", "id": id}
    return templates.TemplateResponse("kiosk_log.html", context)
