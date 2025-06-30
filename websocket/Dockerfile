# Dockerfile.ws
FROM python:3.10-slim

# Install system dependencies and SSL certificates
RUN apt-get update && \
    apt-get install -y gcc build-essential && \
    apt-get clean

WORKDIR /app

COPY . /app

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY init-db.sh /init-db.sh
RUN chmod +x /init-db.sh

RUN pip install --no-cache-dir -r requirements.txt

# Make sure Django env is available (if needed)
ENV PYTHONUNBUFFERED=1

CMD ["python", "websocket/main.py"]
