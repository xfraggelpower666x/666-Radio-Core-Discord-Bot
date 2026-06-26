module.exports = {
  apps: [{
    name: "666-radiobotai-hybrid",
    script: "main.py",
    interpreter: "python3",
    args: "-u",
    cwd: __dirname,
    autorestart: true,
    watch: false,
    max_restarts: 30,
    restart_delay: 5000,
    exp_backoff_restart_delay: 100,
    kill_timeout: 10000,
    env: {
      PYTHONUNBUFFERED: "1"
    }
  }]
};
