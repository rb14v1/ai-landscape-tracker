# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid 1000 --create-home appuser
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
WORKDIR /app/src
CMD ["python", "crawler.py"]
