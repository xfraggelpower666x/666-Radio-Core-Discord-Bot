# 666RadioCoreDJ | Dockerfile
# Erstellt: 2026-06-03
# Geändert: 2026-06-03
# Zweck: Container-Start für den umgebauten Discord-Radio-Control-Bot.
FROM node:20-bookworm-slim

WORKDIR /usr/src/666RadioCoreDJ
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
CMD ["node", "index.js"]
