# Native Deployment (FastAPI + Optional Flask) Non-Docker

This directory provides scripts, systemd units, nginx reverse proxy sample, and CI workflow to run the platform natively (no Docker). FastAPI is primary; legacy Flask subscription backend can run in parallel.

## Quick Deploy (Ad-hoc)
```bash
bash native_deploy/deploy_fastapi.sh
```
Environment variables you can override:
- PORT (default 8000)
- WORKERS (gunicorn workers, default 4)
- HOST (bind host, default 0.0.0.0)

Logs: `logs/` directory (access.log, error.log, console.out, fastapi.pid).

Stop current instance:
```bash
kill $(cat logs/fastapi.pid)
```

## Systemd Installation (FastAPI)
1. Copy code to `/opt/mapmystandards` (or desired path):
```bash
sudo mkdir -p /opt/mapmystandards
sudo rsync -a --exclude .git ./ /opt/mapmystandards/
cd /opt/mapmystandards
bash native_deploy/deploy_fastapi.sh
```
2. Install service unit:
```bash
sudo cp native_deploy/systemd-a3e-fastapi.service /etc/systemd/system/a3e-fastapi.service
sudo systemctl daemon-reload
sudo systemctl enable a3e-fastapi --now
```
3. Check status:
```bash
systemctl status a3e-fastapi
journalctl -u a3e-fastapi -n 100 --no-pager
```

### Flask (Legacy) Systemd Unit
If you need the legacy subscription backend as a managed service:
```bash
sudo cp native_deploy/systemd-flask-subscription.service /etc/systemd/system/mapmystandards-flask.service
sudo systemctl daemon-reload
sudo systemctl enable mapmystandards-flask --now
systemctl status mapmystandards-flask
```

## Switching Between FastAPI and Legacy Flask (Ad-hoc)
The native script deploys FastAPI (`src.a3e.main:app`). Legacy Flask (`subscription_backend.py`) still exists; if you must run it manually:
```bash
python3 -m venv flask_env
source flask_env/bin/activate
pip install -r requirements.txt
python subscription_backend.py
```
(Consider the provided parallel systemd unit if needed.) You now also have `systemd-flask-subscription.service`.

## Health Verification
```bash
curl -I http://localhost:8000/landing
curl -I http://localhost:8000/favicon.ico
```
Expect 200 (or 204 for favicon if no file) and HTML for landing.

## Nginx Reverse Proxy
An example config is provided in `nginx-example.conf` (FastAPI on 8000, Flask on 8001). After adapting domains/TLS:
```bash
sudo cp native_deploy/nginx-example.conf /etc/nginx/sites-available/mapmystandards.conf
sudo ln -s /etc/nginx/sites-available/mapmystandards.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```
Zero-downtime: start new gunicorn on a free port, update upstream block, reload nginx, stop old.

## Updating Code
```bash
cd /opt/mapmystandards
git pull
bash native_deploy/deploy_fastapi.sh
```

## Troubleshooting
- Health check fails: inspect `logs/error.log` and `logs/console.out`.
- Port in use: change `PORT` variable or stop existing process.
- Missing dependencies: re-run `deploy_fastapi.sh` (it reinstalls requirements).
- Flask systemd logs: `flask.out` / `flask.err` in `/opt/mapmystandards/logs`.

## Security Notes
- Run behind a reverse proxy terminating TLS.
- Set secrets via systemd `Environment=` or `EnvironmentFile=`.
- Restrict file permissions; run under non-root (www-data) user.

## CI Packaging
GitHub Actions workflow `.github/workflows/native_deploy.yml` builds & tests, packages a tarball artifact, and optionally remote deploys via SSH (needs secrets: DEPLOY_HOST, DEPLOY_USER, DEPLOY_KEY).
