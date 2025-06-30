# Dockerfile.ws
FROM python:3.10-slim

# Install system dependencies and SSL certificates
RUN apt-get update && \
    apt-get install -y gcc build-essential && \
    apt-get clean

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Make sure Django env is available (if needed)
ENV PYTHONUNBUFFERED=1

CMD ["python", "websocket/main.py"]
