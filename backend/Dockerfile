FROM python:3.10-slim

WORKDIR /app

# Dependencias del sistema (OpenCV necesita libGL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY shared/ ./shared/
COPY ai/ ./ai/
COPY backend/ ./backend/
COPY .env .env

# Exponer el puerto de uvicorn
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
