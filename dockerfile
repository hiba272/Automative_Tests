FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# 🔧 Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y android-sdk-platform-tools adb
RUN apt update && apt install -y \
    gcc \
    portaudio19-dev \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    libglib2.0-dev \
    ffmpeg \
    curl \
    gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# 🔧 Installer Node.js + Appium
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g appium && \
    rm -rf /var/lib/apt/lists/*

# 📁 Définir le dossier de travail
WORKDIR /app

# 📂 Copier les fichiers du projet
COPY . .

# 🐍 Installer les dépendances Python avec le bon index pour paddlepaddle
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt -f https://www.paddlepaddle.org.cn/whl/linux/cpu/avx/stable.html

# 🖥️ Entrée par défaut
CMD ["bash"]
