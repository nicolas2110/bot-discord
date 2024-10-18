# Usa una imagen base de Python
FROM python:3.9-slim

# Actualiza el sistema e instala FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Establece el directorio de trabajo
WORKDIR /app

# Copia todos los archivos del repositorio a la imagen
COPY . /app

# Instala las dependencias del archivo requirements.txt
RUN pip install -r requirements.txt

# Expone el puerto necesario (opcional, por si tu aplicación lo requiere)
EXPOSE 5000

# Comando para ejecutar el bot de Discord
CMD ["python", "discbot.py"]
