
import streamlit as st
import requests
import tempfile
import subprocess
import os

st.set_page_config(page_title="AI Secretary", layout="wide")

HF_TOKEN = os.getenv("HF_TOKEN")  # HuggingFace token из Streamlit Secrets

# --- Заголовок ---
st.title("🤖 AI Secretary")
st.markdown("Загрузите аудио или видео файл, чтобы распознать задачи и отправить их в Jira.")

# --- Загрузка файла ---
uploaded_file = st.file_uploader("Загрузите аудио/видео (mp3, wav, ogg, m4a, mp4, mkv)", 
                                 type=["mp3", "wav", "ogg", "m4a", "mp4", "mkv"])

def extract_audio(video_path, audio_path):
    # Извлекаем аудио из видео с помощью ffmpeg
    cmd = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3", audio_path]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def transcribe(audio_path):
    # Распознавание текста через HuggingFace Whisper API
    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-small"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    with open(audio_path, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()

def extract_tasks(text):
    # Примитивное выделение задач из текста
    tasks = []
    for line in text.split("\n"):
        if any(word in line.lower() for word in ["сделать", "подготовить", "отправить", "создать", "написать"]):
            tasks.append(line.strip())
    return tasks

def create_jira_task(base_url, email, token, project_key, summary):
    # Создание задачи в Jira
    url = f"{base_url}/rest/api/3/issue"
    auth = (email, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": "Task"}
        }
    }
    response = requests.post(url, auth=auth, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

if uploaded_file:
    st.audio(uploaded_file, format="audio/mp3")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Если видео — извлекаем аудио
    if uploaded_file.type in ["video/mp4", "video/x-matroska"]:
        audio_path = tmp_path + ".mp3"
        with st.spinner("Извлекаем аудио из видео..."):
            extract_audio(tmp_path, audio_path)
    else:
        audio_path = tmp_path

    # Распознавание
    if st.button("🎤 Распознать и извлечь задачи"):
        with st.spinner("Распознаём аудио..."):
            try:
                result = transcribe(audio_path)
                text = result.get("text", "")
                language = result.get("language", "неизвестно")
                st.success(f"Распознанный язык: {language}")
                st.text_area("Распознанный текст:", text, height=200)

                tasks = extract_tasks(text)
                st.subheader("📌 Извлечённые задачи")
                if tasks:
                    for t in tasks:
                        st.write(f"- {t}")
                else:
                    st.info("Задачи не найдены.")

                # --- Jira блок ---
                st.subheader("🔗 Отправка в Jira")
                jira_base = st.text_input("Jira Base URL", placeholder="https://yourcompany.atlassian.net")
                jira_email = st.text_input("Email", placeholder="you@example.com")
                jira_token = st.text_input("API Token", type="password")
                jira_project = st.text_input("Project Key", placeholder="TEST")

                if st.button("📤 Отправить задачи в Jira"):
                    if jira_base and jira_email and jira_token and jira_project and tasks:
                        created = []
                        for task in tasks:
                            issue = create_jira_task(jira_base, jira_email, jira_token, jira_project, task)
                            created.append(issue["key"])
                        st.success("Все задачи успешно созданы ✅")
                        st.write("Созданные задачи:", created)
                    else:
                        st.error("Заполните все поля и убедитесь, что есть задачи.")

            except Exception as e:
                st.error(f"Ошибка распознавания: {e}")
