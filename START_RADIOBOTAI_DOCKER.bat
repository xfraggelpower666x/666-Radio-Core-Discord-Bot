services:
  bot:
    container_name: 666-radiobotai
    build: .
    restart: unless-stopped
    env_file: .env
    depends_on:
      - mongo
      - lavalink
    volumes:
      - ./logs:/app/logs
      - ./settings.json:/app/settings.json:ro

  lavalink:
    image: ghcr.io/lavalink-devs/lavalink:4
    container_name: 666-radiobotai-lavalink
    restart: unless-stopped
    volumes:
      - ./lavalink/application.yml:/opt/Lavalink/application.yml:ro
    expose:
      - "2333"
    ports:
      - "2333:2333"

  mongo:
    image: mongo:7
    container_name: 666-radiobotai-mongo
    restart: unless-stopped
    volumes:
      - mongo-data:/data/db

volumes:
  mongo-data:
