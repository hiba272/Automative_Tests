# 1. Image officielle Python
FROM python:3.11-slim

# 2. Ne pas poser de questions pendant l'install
ENV DEBIAN_FRONTEND=noninteractive

# 3. Installer Node.js et Appium
RUN apt-get update && apt-get install -y curl gnupg2 && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g appium

# 4. Définir répertoire de travail
WORKDIR /app

# 5. Copier ton projet dans l'image
COPY . .

# 6. Installer dépendances Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# 7. Lancer Appium automatiquement et ouvrir bash
CMD ["sh", "-c", "appium & exec bash"]
