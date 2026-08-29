# Base Image
FROM python:3.12-slim

# Prevents Python from writing pyc files & buffers stdout (good for logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

#INSTAL dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#COPy the rest of the app
COPY . .
EXPOSE 8000

#use uvicorn to run

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
