import os
import re
import json
import tempfile
import requests
import streamlit as st
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")

ACTION_WORDS = r"(сделать|подготовить|написать|позвонить|отправить|проверить|собрать|запланировать|создать|оформить|утвердить|согласовать|исправить|обновить|добавить|внедрить|исследовать|поставить|созвониться|перенести)"

# ---------------- Utils ----------------
def transcribe_with_openai(file_bytes: bytes, filename: str, language: str):
    if not OPENAI_API_KEY:
        st.error("OpenAI API key not configured")
        return None
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    form = {"model": (None, "whisper-1"), "language": (None, language or "ru")}
    files = {"file": (filename or "audio.wav", file_bytes, "application/octet-stream")}
    try:
        resp = requests.post(url, headers=headers, files=files, data=form, timeout=300)
        resp.raise_for_status()
        return (resp.json().get("text") or "").strip()
    except Exception as e:
        st.error(f"OpenAI transcription error: {e}")
        return None

def extract_tasks_with_gpt(text: str):
    if not OPENAI_API_KEY:
        return []
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Извлеки задачи из текста и верни JSON строго формата {\"tasks\":[{\"title\":\"...\",\"description\":\"...\"}]}"},
            {"role": "user", "content": text or ""},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=120)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return data.get("tasks", [])
    except Exception as e:
        st.warning(f"GPT extractor fallback: {e}")
        return []

def extract_tasks_simple(text: str):
    tasks = []
    for sent in re.split(r"[\\n\\r\\.!?]", text or ""):
        s = sent.strip(" \\t-•—")
        if len(s) >= 8 and re.search(ACTION_WORDS, s, flags=re.I):
            tasks.append({"title": s[:120], "description": s})
    return tasks

def jira_connect(base_url, email, api_token):
    try:
        from jira import JIRA
    except Exception:
        st.error("Package 'jira' not installed")
        return None
    try:
        return JIRA(server=base_url, basic_auth=(email, api_token))
    except Exception as e:
        st.error(f"Jira connection error: {e}")
        return None

# ---------------- UI ----------------
st.set_page_config(page_title="AI Secretary (Streamlit Cloud)", layout="wide")
st.title("🤖 ИИ‑секретарь (Zoom/Meet → Jira)")

ss = st.session_state
if "transcript" not in ss: ss["transcript"] = ""
if "tasks" not in ss: ss["tasks"] = []
if "jira_links" not in ss: ss["jira_links"] = []

st.subheader("1) Загрузите аудио и распознайте")
audio_file = st.file_uploader("Аудио (mp3, wav, m4a)", type=["mp3","wav","m4a"])
language = st.text_input("Язык транскрипции", value="ru")
if st.button("🎤 Распознать и извлечь задачи", disabled=not audio_file):
    raw = audio_file.read()
    ss["transcript"] = transcribe_with_openai(raw, audio_file.name, language) or ""
    ss["tasks"] = extract_tasks_with_gpt(ss["transcript"]) or extract_tasks_simple(ss["transcript"])

st.subheader("2) Транскрибированный текст")
st.text_area("Текст встречи", key="transcript", height=220)

st.subheader("3) Извлечённые задачи")
if ss["tasks"]:
    st.json(ss["tasks"])
else:
    st.info("Список задач появится после распознавания.")

st.subheader("4) Отправить задачи в Jira")
jira_base_url = st.text_input("Jira Base URL", value=JIRA_BASE_URL)
jira_email = st.text_input("Jira Email", value=JIRA_EMAIL)
jira_api_token = st.text_input("Jira API Token", value=JIRA_API_TOKEN, type="password")
jira_project_key = st.text_input("Project Key", value=JIRA_PROJECT_KEY)

if st.button("📤 Отправить задачи в Jira", disabled=len(ss["tasks"])==0):
    jira = jira_connect(jira_base_url, jira_email, jira_api_token)
    if jira:
        links = []
        for t in ss["tasks"]:
            try:
                issue = jira.create_issue(
                    project=jira_project_key,
                    summary=t["title"][:120],
                    description=t["description"],
                    issuetype={"name": "Task"},
                )
                links.append(f"{jira_base_url.rstrip('/')}/browse/{issue.key}")
            except Exception as e:
                st.error(f"Ошибка создания задачи: {e}")
        ss["jira_links"] = links
        if links:
            st.success("✅ Задачи отправлены в Jira")
            for l in links:
                st.write(l)
