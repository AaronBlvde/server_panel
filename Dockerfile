FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Копируем зависимости сначала, чтобы кешировать слой
COPY requirements.txt .

# Устанавливаем зависимости + watchdog для горячей перезагрузки
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install watchdog

# Копируем весь код приложения
COPY . .

# Переменные окружения для Flask
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_ENV=development

# Запуск Flask с авто-перезагрузкой при изменениях
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]
