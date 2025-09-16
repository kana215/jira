
# 🤖 AI Secretary

## Возможности
- Загрузка аудио и видео файлов (mp3, wav, ogg, m4a, mp4, mkv)
- Автоматическое извлечение аудио из видео
- Распознавание текста через HuggingFace Whisper API
- Определение языка
- Извлечение задач из текста
- Отправка задач в Jira

## Установка и запуск локально
```bash
git clone <repo>
cd ai_secretary_final_streamlit
pip install -r requirements.txt
streamlit run main.py
```

## Деплой на Streamlit Cloud
1. Создайте репозиторий на GitHub и залейте файлы.
2. Подключите репозиторий к [Streamlit Cloud](https://share.streamlit.io).
3. В настройках добавьте Secrets:

```
HF_TOKEN="hf_xxxxxxxxx"
```

Пользователи сами вводят свои данные Jira при работе с сайтом.
