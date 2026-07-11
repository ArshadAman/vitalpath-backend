# --- Base Stage ---
FROM python:3.11-slim AS base

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=off     PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip &&     pip install -r requirements.txt

# --- Development Stage ---
FROM base AS development
ENV APP_ENV=local
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Production Stage ---
FROM base AS production
ENV APP_ENV=production

# Create non-root user for security
RUN groupadd -g 10001 appuser &&     useradd -u 10001 -g appuser -d /home/appuser -m appuser

# Copy code
COPY . .
RUN chown -R appuser:appuser /workspace

USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
