FROM python:3.8-slim

# Install required libraries and packages
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install torch==1.10.0 torchvision==0.11.1 torchaudio==0.10.0 -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install opencv-python-headless==4.5.5.64 && \
    pip install ultralytics fastapi uvicorn aiokafka

COPY . /app
WORKDIR /app

CMD ["python", "orchestrator_service.py"]
