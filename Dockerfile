    # Dockerfile

    FROM python:3.11-slim

    # Set working directory
    WORKDIR /app

    # Set PYTHONPATH so that /app/app becomes the root
    ENV PYTHONPATH="/app/app"

    # Install system dependencies
    RUN apt-get update && apt-get install -y gcc libpq-dev

    # Install Python dependencies
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # Copy the application code
    COPY ./app ./app

    # Start command for FastAPI server (only for web container)
    # CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
