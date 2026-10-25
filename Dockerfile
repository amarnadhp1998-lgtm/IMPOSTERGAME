FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY bot.py game.py config.example.py ./
# Supply a token-free runtime config; the actual token is provided by the host.
COPY config.example.py ./config.py

CMD ["python", "bot.py"]
