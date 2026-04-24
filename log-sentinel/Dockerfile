FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir PyYAML prometheus_client

COPY . /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser && \
	chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["python", "sentinel.py"]
