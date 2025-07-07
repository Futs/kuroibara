#!/bin/bash

# Start the development environment
docker compose -f docker-compose.dev.yml up -d

echo "Development environment started!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Documentation: http://localhost:8000/api/docs"
echo "Mailhog: http://localhost:8025"
