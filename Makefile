# Emotech Quiz Game - Docker Management Makefile

.PHONY: help build up down restart logs clean dev prod test

# Default target
help:
	@echo "Emotech Quiz Game - Docker Management Commands"
	@echo "=============================================="
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev          - Start development environment"
	@echo "  make dev-build    - Build development containers"
	@echo "  make dev-logs     - Show development logs"
	@echo "  make dev-down     - Stop development environment"
	@echo ""
	@echo "Production Commands:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build production containers"
	@echo "  make prod-logs    - Show production logs"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean        - Remove all containers, volumes, and images"
	@echo "  make logs         - Show logs for all services"
	@echo "  make restart      - Restart all services"
	@echo "  make test         - Run backend tests"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"
	@echo "  make shell-mongo  - Open shell in MongoDB container"
	@echo ""

# Development environment
dev: dev-build
	docker-compose -f docker-compose.dev.yml up -d
	@echo "🚀 Development environment started!"
	@echo "📱 Frontend: http://localhost:3000"
	@echo "🔧 Backend API: http://localhost:8001"
	@echo "🗄️  MongoDB Express: http://localhost:8081"
	@echo "📊 MongoDB: localhost:27017"

dev-build:
	docker-compose -f docker-compose.dev.yml build

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

dev-down:
	docker-compose -f docker-compose.dev.yml down

# Production environment
prod: prod-build
	docker-compose up -d
	@echo "🚀 Production environment started!"
	@echo "🌐 Application: http://localhost"
	@echo "📱 Frontend: http://localhost:3000"
	@echo "🔧 Backend API: http://localhost:8001"
	@echo "🗄️  MongoDB Express: http://localhost:8081"

prod-build:
	docker-compose build

prod-logs:
	docker-compose logs -f

prod-down:
	docker-compose down

# Utility commands
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed!"

logs:
	docker-compose logs -f

restart:
	docker-compose restart

# Testing
test:
	@echo "🧪 Running backend tests..."
	docker-compose exec backend python -m pytest -v

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-mongo:
	docker-compose exec mongodb mongosh

# Database management
db-backup:
	@echo "💾 Creating database backup..."
	docker-compose exec mongodb mongodump --out /data/backup/$(shell date +%Y%m%d_%H%M%S)
	@echo "✅ Backup completed!"

db-restore:
	@echo "📥 Restoring database from backup..."
	@read -p "Enter backup directory name: " backup_dir; \
	docker-compose exec mongodb mongorestore /data/backup/$$backup_dir
	@echo "✅ Restore completed!"

# Health checks
health:
	@echo "🏥 Checking service health..."
	@echo "Backend:"
	@curl -f http://localhost:8001/api/ || echo "❌ Backend not responding"
	@echo "Frontend:"
	@curl -f http://localhost:3000/ || echo "❌ Frontend not responding"
	@echo "MongoDB:"
	@docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" || echo "❌ MongoDB not responding"

# Development shortcuts
dev-restart: dev-down dev
prod-restart: prod-down prod

# Quick access to services
frontend:
	@echo "📱 Opening frontend..."
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

backend:
	@echo "🔧 Opening backend API docs..."
	@open http://localhost:8001/docs 2>/dev/null || xdg-open http://localhost:8001/docs 2>/dev/null || echo "Please open http://localhost:8001/docs in your browser"

mongo-express:
	@echo "🗄️  Opening MongoDB Express..."
	@open http://localhost:8081 2>/dev/null || xdg-open http://localhost:8081 2>/dev/null || echo "Please open http://localhost:8081 in your browser" 