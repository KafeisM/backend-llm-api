FROM python:3.13-slim

WORKDIR /app

# Configurar variables de entorno óptimas para Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8080

# Instalar dependencias primero (cache de capa Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente completo
COPY . .

# Exponer el puerto por defecto
EXPOSE 8080

# Ejecutar el servidor ASGI
CMD ["sh", "-c", "uvicorn app.main:app --host $APP_HOST --port $APP_PORT"]
