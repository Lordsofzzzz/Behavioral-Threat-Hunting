FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser && \
	chown -R appuser:appuser /app

USER appuser

EXPOSE 8888

CMD ["python", "sentinel.py"]
