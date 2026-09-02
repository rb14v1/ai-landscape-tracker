
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

CMD ["python", "crawler.py"]

