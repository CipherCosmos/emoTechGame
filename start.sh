#!/bin/sh

# Set default port if not provided
export PORT=${PORT:-3000}

# Update nginx configuration with the correct port
sed -i "s/listen 3000;/listen $PORT;/" /etc/nginx/conf.d/default.conf

# Start backend in background
cd /app/backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload &

# Start nginx
nginx -g "daemon off;" 