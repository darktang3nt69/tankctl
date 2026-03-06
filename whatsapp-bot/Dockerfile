FROM node:20-bullseye

WORKDIR /app

# Install system dependencies for Puppeteer/Chrome
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-sandbox \
    libxss1 \
    libnss3 \
    libgconf-2-4 \
    libatk-bridge2.0-0 \
    libgbm-dev \
    libxkbcommon0 \
    xdg-utils \
    fonts-liberation \
    libappindicator1 \
    libxext6 \
    libxinerama1 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Install npm dependencies
RUN npm ci --omit=dev

# Copy app files
COPY . .

# Create session directory
RUN mkdir -p /app/session

# Set executable permissions
RUN chmod +x /app/bot.js

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Start bot
CMD ["node", "bot.js"]
