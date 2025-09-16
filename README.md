# AI Secretary (Streamlit Cloud)

## Как запустить на Streamlit Cloud

1. Залей файлы `main.py`, `requirements.txt`, `.env.example` в репозиторий GitHub.
2. На https://share.streamlit.io выбери этот репозиторий.
3. В настройках добавь переменные окружения (из .env):
   - `OPENAI_API_KEY`
   - `JIRA_BASE_URL`
   - `JIRA_EMAIL`
   - `JIRA_API_TOKEN`
   - `JIRA_PROJECT_KEY`
4. Нажми Deploy — сайт будет доступен онлайн.

## Локальный запуск

```bash
python -m venv venv
source venv/bin/activate  # или .\venv\Scripts\activate на Windows
pip install -r requirements.txt
streamlit run main.py
```
