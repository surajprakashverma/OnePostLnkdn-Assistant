import truststore
truststore.inject_into_ssl()

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import settings
from app.services.auth_service import verify_credentials, create_session_token

router = APIRouter()

_LT = chr(60)
_GT = chr(62)
_Q = chr(34)

FORM_OPEN = _LT + "form action=" + _Q + "/login" + _Q + " method=" + _Q + "post" + _Q + _GT
FORM_CLOSE = _LT + "/form" + _GT

FAVICON_LINKS = (
    _LT + "link rel=" + _Q + "icon" + _Q + " type=" + _Q + "image/x-icon" + _Q + " href=" + _Q + "/static/favicon.ico" + _Q + _GT +
    _LT + "link rel=" + _Q + "icon" + _Q + " type=" + _Q + "image/png" + _Q + " sizes=" + _Q + "32x32" + _Q + " href=" + _Q + "/static/favicon-32x32.png" + _Q + _GT +
    _LT + "link rel=" + _Q + "icon" + _Q + " type=" + _Q + "image/png" + _Q + " sizes=" + _Q + "16x16" + _Q + " href=" + _Q + "/static/favicon-16x16.png" + _Q + _GT +
    _LT + "link rel=" + _Q + "apple-touch-icon" + _Q + " href=" + _Q + "/static/apple-touch-icon.png" + _Q + _GT
)

LOGO_IMG = (
    _LT + "img src=" + _Q + "/static/onepostlnkdn-logo-full.png" + _Q +
    " alt=" + _Q + "OnePostLnkdn Assistant" + _Q +
    " style=" + _Q + "max-width:100%;height:auto;margin-bottom:22px;" + _Q + _GT
)

LOGIN_FORM_HTML = (
    "<!DOCTYPE html><html><head><meta charset=" + _Q + "utf-8" + _Q + ">"
    "<title>OnePostLnkdn Assistant</title>"
    + FAVICON_LINKS +
    "<style>"
    "* { box-sizing: border-box; margin: 0; padding: 0; }"
    "body {"
    "  font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif;"
    "  background: linear-gradient(135deg, #0A66C2 0%, #063E7B 55%, #021B36 100%);"
    "  min-height: 100vh;"
    "  display: flex;"
    "  align-items: center;"
    "  justify-content: center;"
    "  padding: 20px;"
    "}"
    ".card {"
    "  background: #ffffff;"
    "  width: 100%;"
    "  max-width: 380px;"
    "  border-radius: 16px;"
    "  padding: 40px 34px;"
    "  box-shadow: 0 20px 60px rgba(0,0,0,0.35);"
    "  text-align: center;"
    "}"
    ".subtitle { color: #7a7f8c; font-size: 13.5px; margin-bottom: 28px; }"
    "input {"
    "  width: 100%; padding: 13px 14px; margin-bottom: 14px;"
    "  border: 1.5px solid #e2e5eb; border-radius: 9px; font-size: 14px;"
    "  outline: none; transition: border-color 0.15s ease;"
    "}"
    "input:focus { border-color: #0A66C2; }"
    "button {"
    "  width: 100%; padding: 13px; border: none; border-radius: 9px;"
    "  background: linear-gradient(135deg, #0A66C2, #0850a0);"
    "  color: #fff; font-size: 15px; font-weight: 600; cursor: pointer;"
    "  margin-top: 6px; transition: opacity 0.15s ease;"
    "}"
    "button:hover { opacity: 0.9; }"
    ".error-box {"
    "  background: #FDECEC; color: #B00020; padding: 10px 14px;"
    "  border-radius: 8px; font-size: 13px; margin-bottom: 16px; text-align: left;"
    "}"
    ".footer-note { margin-top: 22px; font-size: 11.5px; color: #b0b4bd; }"
    "</style></head><body>"
    "<div class=" + _Q + "card" + _Q + ">"
    + LOGO_IMG +
    "<p class=" + _Q + "subtitle" + _Q + ">Sign in to manage your roadmap</p>"
    "{error_message}"
    + FORM_OPEN +
    "<input type=" + _Q + "text" + _Q + " name=" + _Q + "username" + _Q + " placeholder=" + _Q + "Username" + _Q + " required>"
    "<input type=" + _Q + "password" + _Q + " name=" + _Q + "password" + _Q + " placeholder=" + _Q + "Password" + _Q + " required>"
    "<button type=" + _Q + "submit" + _Q + ">Log In</button>"
    + FORM_CLOSE +
    "<p class=" + _Q + "footer-note" + _Q + ">Automated LinkedIn content pipeline</p>"
    "</div></body></html>"
)


@router.get("/login", response_class=HTMLResponse)
def login_form():
    return LOGIN_FORM_HTML.replace("{error_message}", "")


@router.post("/login")
def login_submit(username: str = Form(...), password: str = Form(...)):
    if not verify_credentials(username, password):
        error_html = "<div class=" + chr(34) + "error-box" + chr(34) + ">Invalid username or password</div>"
        return HTMLResponse(
            LOGIN_FORM_HTML.replace("{error_message}", error_html),
            status_code=401,
        )

    token = create_session_token(username)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=settings.SESSION_TOKEN_EXPIRE_HOURS * 3600,
        samesite="lax",
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    return response