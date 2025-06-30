FROM python:3.10-slim

# Install system dependencies and SSL certificates
RUN apt-get update && \
    apt-get install -y gcc build-essential && \
    apt-get clean

# Set work directory
WORKDIR /app

# Copy files
COPY . /app

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY init-db.sh /init-db.sh
RUN chmod +x /init-db.sh

# Install Python dependencies
RUN pip install --upgrade --trusted-host pypi.org --trusted-host files.pythonhosted.org pip
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pip-system-certs

# Run the bot
CMD ["python", "manage.py", "runbot"]
