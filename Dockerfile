FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs.
# TZ sets the container timezone to Asia/Jakarta (WIB).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Jakarta

WORKDIR /app

# Install tzdata so TZ resolves, then configure the local time zone
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Jakarta /etc/localtime \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Run as a non-root user
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
