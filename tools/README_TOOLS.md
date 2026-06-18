# Tools

Repo-interner Platz fuer Reparatur-, Audit- und Hilfsskripte.

Werkzeuge muessen additiv integriert werden und duerfen keine bestehende
Projektstruktur ersetzen.

## check_radiobotai_ready.ps1

Prueft lokal, ob der Bot startbereit ist:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\check_radiobotai_ready.ps1
```

Der Check zeigt keine Secret-Werte an. Er meldet nur, ob `.env`, Discord-Token,
Client-ID, Stream-URL, Docker, Node und Python vorhanden sind.

## install_docker_desktop_windows.ps1

Installiert Docker Desktop fuer Windows mit WSL 2 ueber `winget` und prueft
danach `docker`, `docker compose` und optional `hello-world`.

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install_docker_desktop_windows.ps1
```

Alternativ per Doppelklick:

```text
tools\install_docker_desktop_windows.bat
```

Das Skript startet sich bei Bedarf selbst mit Administratorrechten. Falls
Windows Features neu aktiviert wurden, ist danach eventuell ein Neustart noetig.
