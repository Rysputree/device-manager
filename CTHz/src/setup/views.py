from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse)
async def setup_wizard(request: Request):
    return templates.TemplateResponse("setup/wizard.html", {"request": request})
