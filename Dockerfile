FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости + watchdog для горячей перезагрузки
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install watchdog

# Копируем весь код приложения
COPY . .

# Переменные окружения для Flask
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

# Запуск Flask с авто-перезагрузкой при изменениях
CMD ["flask", "run", "--reload"]
