# Usa immagine ufficiale Python 3.11 slim
FROM python:3.11-slim

# Imposta la working directory
WORKDIR /app

# Copia i file del progetto nel container
COPY . /app

# Installa dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta 80
EXPOSE 80

# Comando per avviare il server
CMD ["python", "mock-mes.py"]
