# 666RadioCoreDJ | Makefile
# Erstellt: 2026-06-03
# Geändert: 2026-06-03
# Zweck: Einfache Docker-Helfer.

IMAGE=666-radio-core-dj

build:
	docker build -t $(IMAGE) .

start:
	docker run --rm --name $(IMAGE) --env-file .env $(IMAGE)

stop:
	docker stop $(IMAGE)
