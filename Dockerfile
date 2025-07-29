# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Install system dependencies for both iOS and Android support
RUN apt-get update && apt-get install -y \
    # iOS support (pymobiledevice3)
    libusb-1.0-0-dev \
    usbmuxd \
    openssl \
    libssl-dev \
    pkg-config \
    gcc \
    curl \
    # Android support (ADB)
    android-tools-adb \
    android-tools-fastboot \
    # Additional utilities
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Create directory for device state files
RUN mkdir -p /tmp && chmod 777 /tmp

# Run the Flask application as root (required for device access)
CMD ["python", "app.py"] 