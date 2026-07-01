FROM node:20-bookworm-slim

WORKDIR /app

# Instala dependencias com lockfile para builds reprodutiveis.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]