# Utiliser une image Python officielle légère
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Variables d'environnement pour optimiser Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/requirements.txt && \
    pip install --no-cache-dir requests

# Copier le code de l'application
COPY . .

# La base de données sera initialisée au runtime par l'application

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Exposer le port Streamlit
EXPOSE 8501

# Configuration Streamlit
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Point d'entrée de l'application
CMD ["python", "run_app.py"]
