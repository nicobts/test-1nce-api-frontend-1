FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
# Copy application files
COPY . .

# Expose ports
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["python", "run_full_app.py"]
