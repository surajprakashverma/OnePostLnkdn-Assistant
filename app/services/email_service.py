import truststore
truststore.inject_into_ssl()

import requests

from app.core.config import settings

RESEND_API_URL = "https://api.resend.com/emails"

_LT = chr(60)
_GT = chr(62)
_Q = chr(34)


def _build_button(url, label, bg_color):
    return (
        _LT + "a href=" + _Q + url + _Q +
        " style=" + _Q +
        "background:" + bg_color + ";color:#ffffff;padding:10px 22px;text-decoration:none;"
        "border-radius:6px;margin-right:10px;display:inline-block;font-weight:bold;" +
        _Q + _GT + label + _LT + "/a" + _GT
    )


def send_approval_email(post_log_id, topic, subtopic, draft_text, score, attempts, met_threshold, approve_url, reject_url):
    subject_prefix = "PASS" if met_threshold else "REVIEW"
    subject = "[" + subject_prefix + "] LinkedIn Post Ready for Review - " + topic + " (Score: " + str(score) + "/10)"

    if met_threshold:
        quality_note = "Quality Score: " + str(score) + "/10 - passed automated QA after " + str(attempts) + " attempt(s)."
    else:
        quality_note = "Quality Score: " + str(score) + "/10 - did NOT meet the auto-QA threshold after " + str(attempts) + " attempts. Please review carefully before approving."

    approve_button = _build_button(approve_url, "Approve and Post", "#0A66C2")
    reject_button = _build_button(reject_url, "Reject", "#B00020")

    topic_line = "Topic: " + topic
    if subtopic:
        topic_line = topic_line + " - " + subtopic

    html_body = (
        "<html><body style=" + chr(39) + "font-family: Arial, sans-serif; max-width: 600px; margin: auto;" + chr(39) + ">"
        "<h2>New LinkedIn Post Draft</h2>"
        "<p><strong>" + topic_line + "</strong></p>"
        "<p><strong>" + quality_note + "</strong></p>"
        "<div style=" + chr(39) + "background:#f4f6fb; padding:16px; border-radius:8px; white-space:pre-wrap; margin:16px 0; border:1px solid #ddd;" + chr(39) + ">"
        + draft_text +
        "</div>"
        "<div style=" + chr(39) + "margin:20px 0;" + chr(39) + ">"
        + approve_button + reject_button +
        "</div>"
        "<p style=" + chr(39) + "font-size:12px;color:#888;" + chr(39) + ">This link expires in "
        + str(settings.APPROVAL_TOKEN_EXPIRE_HOURS) +
        " hours and can only be used once.</p>"
        "</body></html>"
    )

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": "Bearer " + settings.RESEND_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "from": "onboarding@resend.dev",
            "to": [settings.NOTIFY_TO_EMAIL],
            "subject": subject,
            "html": html_body,
        },
        timeout=15,
    )

    if response.status_code >= 400:
        raise RuntimeError("Resend API error (" + str(response.status_code) + "): " + response.text)

    print("Approval email sent to " + settings.NOTIFY_TO_EMAIL + " (post_log_id=" + str(post_log_id) + ")")
