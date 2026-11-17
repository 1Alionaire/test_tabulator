#!/usr/bin/env bash
set -euo pipefail
cd ~/allab
git pull --ff-only
docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f

# ждём до 60 секунд, пока сайт начнёт отвечать
for i in $(seq 1 30); do
  if curl -fsS -o /dev/null -H "Host: allab.tail61e71a.ts.net" http://127.0.0.1:8080/users/login/; then
    echo "Deploy OK"; exit 0
  fi
  sleep 2
done
echo "Site did not come up"
docker compose -f docker-compose.prod.yml logs --tail=50 web
exit 1