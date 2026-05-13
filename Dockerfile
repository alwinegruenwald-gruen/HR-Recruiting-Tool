# Basis-Image – Python 3.11 auf Linux
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Requirements zuerst kopieren und installieren
COPY requirements.txt .
RUN pip install -r requirements.txt

# Restlichen Code kopieren
COPY . .

# Port freigeben
EXPOSE 8501

# App starten
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]