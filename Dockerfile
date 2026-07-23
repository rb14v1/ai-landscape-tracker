FROM python:3.12-slim

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy and install dependencies
COPY crawler/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY crawler/ ./crawler/

# Ensure the data directory exists and is owned by the non-root user
RUN mkdir -p crawler/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

WORKDIR /app/crawler/src

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/healthz').status == 200 else 1)"

CMD ["python", "crawler.py"]
