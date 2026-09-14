import truststore
truststore.inject_into_ssl()

"""
LinkedIn OAuth Routes
----------------------
One-time authorization flow:
  1. Visit /auth/linkedin/login -> redirects you to LinkedIn's consent screen
  2. You click "Allow" -> LinkedIn redirects back to /auth/linkedin/callback with a code
  3. We exchange that code for an access token and fetch your person URN
  4. Both get printed so you can paste them into .env manually (simplest approach for now)
"""
import requests
from fastapi import APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse

from app.core.config import settings

router = APIRouter()

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

SCOPES = "openid profile w_member_social"


@router.get("/auth/linkedin/login")
def linkedin_login():
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "scope": SCOPES,
    }
    query = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())
    return RedirectResponse(url=f"{LINKEDIN_AUTH_URL}?{query}")


@router.get("/auth/linkedin/callback", response_class=HTMLResponse)
def linkedin_callback(code: str = None, error: str = None, error_description: str = None):
    if error:
        return f"<h2>LinkedIn authorization failed</h2><p>{error}: {error_description}</p>"

    # Exchange the authorization code for an access token
    token_response = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )

    if token_response.status_code != 200:
        return f"<h2>Token exchange failed</h2><pre>{token_response.text}</pre>"

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")

    # Fetch the user's profile to get their person URN (needed to author posts)
    userinfo_response = requests.get(
        LINKEDIN_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )

    person_urn = "unknown"
    userinfo_data = {}
    if userinfo_response.status_code == 200:
        userinfo_data = userinfo_response.json()
        sub = userinfo_data.get("sub")
        if sub:
            person_urn = f"urn:li:person:{sub}"

    return f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto;">
        <h2>LinkedIn Authorization Successful</h2>
        <p>Copy these two values into your <code>.env</code> file:</p>
        <div style="background:#f4f6fb; padding:16px; border-radius:8px; border:1px solid #ddd;">
            <p><strong>LINKEDIN_ACCESS_TOKEN=</strong><br><code style="word-break:break-all;">{access_token}</code></p>
            <p><strong>LINKEDIN_PERSON_URN=</strong><br><code>{person_urn}</code></p>
        </div>
        <p style="color:#888;">Token expires in {expires_in} seconds (~{round(expires_in/86400)} days).</p>
        <p>Profile info retrieved: {userinfo_data.get('name', 'N/A')}</p>
    </body></html>
    """