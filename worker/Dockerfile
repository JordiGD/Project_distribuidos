FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    wget \
    build-essential \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .

RUN useradd -m worker
USER worker

CMD ["python", "worker.py"]