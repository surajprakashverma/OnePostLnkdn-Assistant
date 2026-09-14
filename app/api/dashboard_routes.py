import truststore
truststore.inject_into_ssl()

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse

from app.services.auth_service import get_current_user
from app.services.roadmap_run_service import get_status, start_new_run, stop_run

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_LT = chr(60)
_GT = chr(62)
_Q = chr(34)

FAVICON_LINKS = (
    _LT + "link rel=" + _Q + "icon" + _Q + " type=" + _Q + "image/x-icon" + _Q + " href=" + _Q + "/static/favicon.ico" + _Q + _GT +
    _LT + "link rel=" + _Q + "icon" + _Q + " type=" + _Q + "image/png" + _Q + " sizes=" + _Q + "32x32" + _Q + " href=" + _Q + "/static/favicon-32x32.png" + _Q + _GT +
    _LT + "link rel=" + _Q + "icon" + _Q + " type=" + _Q + "image/png" + _Q + " sizes=" + _Q + "16x16" + _Q + " href=" + _Q + "/static/favicon-16x16.png" + _Q + _GT +
    _LT + "link rel=" + _Q + "apple-touch-icon" + _Q + " href=" + _Q + "/static/apple-touch-icon.png" + _Q + _GT
)

LOGOUT_LINK = _LT + "a href=" + _Q + "/logout" + _Q + " class=" + _Q + "logout-link" + _Q + _GT + "Log out" + _LT + "/a" + _GT

LOGO_IMG = (
    _LT + "img src=" + _Q + "/static/onepostlnkdn-logo-full.png" + _Q +
    " alt=" + _Q + "OnePostLnkdn Assistant" + _Q +
    " style=" + _Q + "height:34px;width:auto;display:block;" + _Q + _GT
)


CHAT_UI_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>OnePostLnkdn Assistant</title>
__FAVICON_LINKS__
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    height: 100%;
    overflow: hidden;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif;
    background: linear-gradient(160deg, #eef3fb 0%, #dce7f5 100%);
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .app-shell {
    width: 100%;
    max-width: 720px;
    height: 100vh;
    max-height: 780px;
    display: flex;
    flex-direction: column;
    padding: 16px;
  }
  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, #0A66C2, #063E7B);
    color: #fff; padding: 14px 20px; border-radius: 16px 16px 0 0;
    box-shadow: 0 10px 30px rgba(10,50,100,0.25);
    flex-shrink: 0;
  }
  .brand { display: flex; align-items: center; gap: 12px; }
  .logout-link {
    color: #fff; text-decoration: none; font-size: 12px; opacity: 0.85;
    border: 1px solid rgba(255,255,255,0.4); padding: 5px 11px; border-radius: 20px;
    flex-shrink: 0;
  }
  .logout-link:hover { opacity: 1; background: rgba(255,255,255,0.1); }

  .card-body {
    background: #ffffff; border-radius: 0 0 16px 16px; box-shadow: 0 20px 50px rgba(20,40,80,0.12);
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }

  #chat-window {
    padding: 16px 18px;
    flex: 1;
    overflow-y: auto;
    display: flex; flex-direction: column; gap: 9px;
    background: #f7f9fc;
    min-height: 0;
  }
  .msg-bot, .msg-user {
    padding: 10px 14px; border-radius: 14px; max-width: 82%; font-size: 13.2px;
    line-height: 1.45; white-space: pre-line;
  }
  .msg-bot { background: #ffffff; border: 1px solid #e6eaf1; color: #262b36; align-self: flex-start; border-bottom-left-radius: 4px; }
  .msg-user { background: linear-gradient(135deg, #0A66C2, #0850a0); color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }

  .input-area { padding: 12px 18px; border-top: 1px solid #eef0f4; background: #fff; flex-shrink: 0; }
  .input-row { display: flex; gap: 9px; }
  #chat-input {
    flex: 1; padding: 10px 13px; border-radius: 10px; border: 1.5px solid #e2e5eb;
    font-size: 13.2px; outline: none;
  }
  #chat-input:focus { border-color: #0A66C2; }
  .send-btn {
    padding: 0 20px; border: none; border-radius: 10px;
    background: linear-gradient(135deg, #0A66C2, #0850a0); color: #fff;
    font-weight: 600; font-size: 13px; cursor: pointer;
  }
  .send-btn:hover { opacity: 0.92; }

  .quick-chips { display: flex; gap: 7px; margin-top: 8px; flex-wrap: wrap; }
  .chip {
    background: #eef3fb; color: #0A66C2; padding: 5px 12px; border-radius: 20px;
    font-size: 11.5px; cursor: pointer; border: 1px solid #d7e4f7; font-weight: 500;
  }
  .chip:hover { background: #e1ecfb; }

  .upload-panel {
    padding: 12px 18px; border-top: 1px solid #eef0f4; background: #fbfcfe; flex-shrink: 0;
  }
  .upload-panel h3 { font-size: 11px; color: #5c6270; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }
  .upload-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .upload-row input[type="file"] { font-size: 11.5px; flex: 1; min-width: 140px; }
  .upload-row input[type="number"] {
    width: 62px; padding: 7px 9px; border-radius: 8px; border: 1.5px solid #e2e5eb; font-size: 12.5px;
  }
  .upload-btn {
    padding: 8px 16px; border: none; border-radius: 8px;
    background: #1a1a2e; color: #fff; font-size: 11.5px; font-weight: 600; cursor: pointer;
  }
  .upload-btn:hover { opacity: 0.9; }
  .days-label { font-size: 11.5px; color: #5c6270; }
</style>
</head>
<body>
<div class="app-shell">
  <div class="topbar">
    <div class="brand">
      __LOGO_IMG__
    </div>
    __LOGOUT_LINK__
  </div>

  <div class="card-body">
    <div id="chat-window"></div>

    <div class="input-area">
      <div class="input-row">
        <input type="text" id="chat-input" placeholder="Type a command..." onkeydown="if(event.key==='Enter') sendCommand()">
        <button class="send-btn" onclick="sendCommand()">Send</button>
      </div>
      <div class="quick-chips">
        <div class="chip" onclick="quickSend('status')">Status</div>
        <div class="chip" onclick="quickSend('trigger now')">Trigger Now</div>
        <div class="chip" onclick="quickSend('stop')">Stop Roadmap</div>
      </div>
    </div>

    <div class="upload-panel">
      <h3>Upload a New Roadmap</h3>
      <div class="upload-row">
        <input type="file" id="roadmap-file" accept=".pdf,.docx,.txt">
        <span class="days-label">Days:</span>
        <input type="number" id="num-days" value="30">
        <button class="upload-btn" onclick="uploadRoadmap()">Upload &amp; Start</button>
      </div>
    </div>
  </div>
</div>

<script>
function addMessage(text, sender) {
  const win = document.getElementById("chat-window");
  const div = document.createElement("div");
  div.className = sender === "user" ? "msg-user" : "msg-bot";
  div.innerText = text;
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}

async function sendCommand() {
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;
  addMessage(text, "user");
  input.value = "";

  const res = await fetch("/dashboard/command", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({command: text})
  });
  const data = await res.json();
  addMessage(data.reply, "bot");
}

function quickSend(text) {
  document.getElementById("chat-input").value = text;
  sendCommand();
}

async function uploadRoadmap() {
  const fileInput = document.getElementById("roadmap-file");
  const numDays = document.getElementById("num-days").value;
  if (!fileInput.files.length) { addMessage("Please choose a file first.", "bot"); return; }

  addMessage("Uploading " + fileInput.files[0].name + " for a " + numDays + "-day roadmap...", "user");

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("num_days", numDays);

  const res = await fetch("/dashboard/upload", { method: "POST", body: formData });
  const data = await res.json();
  addMessage(data.reply, "bot");
}

window.onload = () => addMessage("Hi! I am your OnePostLnkdn Assistant. Available commands: status, stop, trigger now. Or upload a new roadmap below.", "bot");
</script>
</body>
</html>
"""

CHAT_UI_HTML = (
    CHAT_UI_HTML_TEMPLATE
    .replace("__FAVICON_LINKS__", FAVICON_LINKS)
    .replace("__LOGOUT_LINK__", LOGOUT_LINK)
    .replace("__LOGO_IMG__", LOGO_IMG)
)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(user: str = Depends(get_current_user)):
    return CHAT_UI_HTML


@router.post("/dashboard/command")
def dashboard_command(payload: dict, user: str = Depends(get_current_user)):
    command = payload.get("command", "").strip().lower()

    if command in ("status", "check status", "current status"):
        status = get_status()
        if not status["active"]:
            return JSONResponse({"reply": status["message"]})
        reply = (
            "Active roadmap: " + str(status["roadmap_filename"]) + "\n"
            "Started: " + str(status["started_at"]) + "\n"
            "Progress: " + str(status["posted_count"]) + " posted, " + str(status["pending_count"]) + " pending approval, out of " + str(status["total_topics"]) + " total days\n"
            "Next topic: " + str(status["next_topic"])
        )
        return JSONResponse({"reply": reply})

    if command in ("stop", "stop roadmap", "stop the roadmap"):
        result = stop_run()
        return JSONResponse({"reply": result["message"]})

    if command in ("trigger now", "run now", "post now", "trigger", "run pipeline", "trigger pipeline", "generate now"):
        from app.agents.pipeline import run_daily_pipeline
        post_log_id = run_daily_pipeline()
        if post_log_id is None:
            return JSONResponse({
                "reply": "Could not trigger the pipeline. Either no roadmap is active, or all topics have already been posted or are pending approval."
            })
        return JSONResponse({"reply": "Pipeline triggered. Draft saved (id=" + str(post_log_id) + ") and approval email sent."})

    return JSONResponse({
        "reply": (
            "I did not understand that. Available commands:\n"
            "- status - check current roadmap progress\n"
            "- stop - stop the current roadmap\n"
            "- trigger now - manually run today's post generation immediately\n"
            "- or use the upload box below to start a new roadmap"
        )
    })


@router.post("/dashboard/upload")
async def dashboard_upload(
    file: UploadFile = File(...),
    num_days: int = Form(...),
    user: str = Depends(get_current_user),
):
    status = get_status()
    if status["active"]:
        return JSONResponse({
            "reply": "A roadmap is already running (" + str(status["roadmap_filename"]) + ", started " + str(status["started_at"]) + "). Please stop it first before starting a new one."
        })

    save_path = UPLOAD_DIR / file.filename
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = start_new_run(str(save_path), num_days)

    try:
        save_path.unlink()
    except OSError:
        pass

    return JSONResponse({"reply": result["message"]})