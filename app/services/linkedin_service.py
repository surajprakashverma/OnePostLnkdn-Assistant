import truststore
truststore.inject_into_ssl()

"""
LinkedIn Service
-----------------
Publishes an approved post to LinkedIn using the Posts API
(https://api.linkedin.com/rest/posts), the current recommended
endpoint that replaced the legacy UGC/Shares APIs.
"""
import requests

from app.core.config import settings

LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_API_VERSION =os.getenv("LINKEDIN_API_VERSION", "202609")  # YYYYMM format, required header


def publish_post(text: str) -> dict:
    """
    Publishes a text-only post to the authenticated user's LinkedIn profile.

    Returns:
        {
          "success": bool,
          "post_urn": str | None,   # e.g. "urn:li:share:12345..."
          "error": str | None,
        }
    """
    headers = {
        "Authorization": f"Bearer {settings.LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": LINKEDIN_API_VERSION,
    }

    payload = {
        "author": settings.LINKEDIN_PERSON_URN,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    response = requests.post(LINKEDIN_POSTS_URL, headers=headers, json=payload, timeout=20)

    if response.status_code == 201:
        # LinkedIn returns the new post's URN in the response header, not the body
        post_urn = response.headers.get("x-restli-id") or response.headers.get("X-RestLi-Id")
        return {"success": True, "post_urn": post_urn, "error": None}

    return {
        "success": False,
        "post_urn": None,
        "error": f"{response.status_code}: {response.text}",
    }
