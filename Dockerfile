FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable (will be overridden by deployment platform)
ENV PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["sh", "-c", "python main.py & sleep 3600"]
