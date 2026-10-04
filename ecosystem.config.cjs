module.exports = {
  apps: [{
    name: 'chronis',
    script: 'bot.py',
    interpreter: 'python3',
    cwd: __dirname,
    autorestart: true,
    stop_exit_codes: [0],
    restart_delay: 3000,
    max_restarts: 50
  }]
};
