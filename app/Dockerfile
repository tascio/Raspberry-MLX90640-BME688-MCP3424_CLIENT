FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libegl1 \
    sshpass \
    ssh \
    && rm -rf /var/lib/apt/lists/*

COPY ./code /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/logs && chmod 755 /app/logs
RUN mkdir -p /app/acquisitions && chmod 755 /app/acquisitions

#CMD ["python", "app.py"]

CMD ["gunicorn", "-w", "1", "-k", "eventlet", "-b", "0.0.0.0:5080", "app:app", "--log-level", "info"]
