FROM python:3.11-slim

WORKDIR /app

# System dependencies for PyMuPDF and psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libmupdf-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/attachments /app/tmp

# Set Python path
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
