#!/bin/sh
set -e

# Start Next.js server in the background
echo "Starting Next.js server..."
cd /app
PORT=3000 HOSTNAME=0.0.0.0 node apps/web/server.js > /tmp/nextjs.log 2>&1 &
NEXTJS_PID=$!

# Wait for Next.js to be ready
echo "Waiting for Next.js to be ready..."
for i in $(seq 1 60); do
  if wget --spider --quiet http://127.0.0.1:3000 2>/dev/null; then
    echo "Next.js is ready!"
    sleep 2
    break
  fi
  if [ $i -eq 60 ]; then
    echo "Next.js failed to start in time"
    echo "Next.js logs:"
    cat /tmp/nextjs.log
    exit 1
  fi
  sleep 1
done

# Start nginx in foreground
echo "Starting nginx..."
exec nginx -g 'daemon off;'
