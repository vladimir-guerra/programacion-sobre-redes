FROM python:3.14-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar Poetry
RUN pip install --no-cache-dir poetry

# Configuración de Poetry: que instale las dependencias en el sistema 
# en lugar de crear un entorno virtual dentro del contenedor
RUN poetry config virtualenvs.create false

# Copiar solo los archivos de dependencias primero
COPY pyproject.toml poetry.lock* ./

# Instalar dependencias
RUN poetry install --no-root --no-interaction --no-ansi

# Copiar el resto del código
COPY . .

CMD ["python", "server.py"]