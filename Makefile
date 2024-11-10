.PHONY: run-all run-backend run-frontend db-reset db-open db-show-tables db-show-schema db-query db-init kill-backend kill-frontend show-logs stop-backend docker-build docker-up docker-down

# Variables
DB_PATH = backend/db/app.db

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-down:
	docker-compose down

# Run services
run-all:
	docker-compose up

run-backend:
	docker-compose up backend

run-frontend:
	cd frontend && npm start

# Stop services
kill-backend:
	@echo "Stopping all backend processes..."
	@# Убиваем процессы на портах более агрессивно
	@for port in 8000 8001 8002; do \
		if lsof -ti :$$port > /dev/null; then \
			echo "Killing process on port $$port"; \
			kill -9 $$(lsof -ti:$$port) 2>/dev/null || true; \
		fi \
	done
	@# Находим и убиваем все процессы Python более агрессивно
	@pgrep -f "python.*backend" | xargs kill -9 2>/dev/null || true
	@pgrep -f "uvicorn" | xargs kill -9 2>/dev/null || true
	@pgrep -f "aiogram" | xargs kill -9 2>/dev/null || true
	@pgrep -f "main.py" | xargs kill -9 2>/dev/null || true
	@pgrep -f "telegram|tg_bot" | xargs kill -9 2>/dev/null || true
	@pgrep -f "python.*bot" | xargs kill -9 2>/dev/null || true
	@# Дополнительная проверка и очистка
	@ps aux | grep -E "python|uvicorn|bot|telegram" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
	@echo "All backend processes should be stopped now"
	@# Финальная проверка
	@if ps aux | grep -E "python|uvicorn|bot|telegram" | grep -v grep; then \
		echo "Warning: Some processes might still be running"; \
	else \
		echo "All processes successfully terminated"; \
	fi

kill-frontend:
	@if lsof -i :3000 > /dev/null; then \
		kill $$(lsof -t -i:3000); \
		echo "Frontend server stopped"; \
	else \
		echo "Frontend server is not running"; \
	fi

# Database commands
db-reset:
	docker-compose exec backend python -c "from app.services.db_service import DatabaseService; DatabaseService().reset_db()"
	@echo "Database has been reset successfully!"

db-init:
	docker-compose exec backend python -c "from app.services.db_service import DatabaseService; DatabaseService()"
	@echo "Database has been initialized successfully!"

db-open:
	@if [ -f $(DB_PATH) ]; then \
		sqlite3 $(DB_PATH) -column -header; \
	else \
		echo "Database file not found at $(DB_PATH)"; \
		exit 1; \
	fi

db-show-tables:
	@if [ -f $(DB_PATH) ]; then \
		echo ".tables" | sqlite3 $(DB_PATH); \
	else \
		echo "Database file not found at $(DB_PATH)"; \
		exit 1; \
	fi

db-show-schema:
	@if [ -f $(DB_PATH) ]; then \
		echo ".schema" | sqlite3 $(DB_PATH); \
	else \
		echo "Database file not found at $(DB_PATH)"; \
		exit 1; \
	fi

db-query:
	@if [ -f $(DB_PATH) ]; then \
		sqlite3 $(DB_PATH) "$(q)"; \
	else \
		echo "Database file not found at $(DB_PATH)"; \
		exit 1; \
	fi

# Tests
test-backend:
	docker-compose exec backend python -m pytest

# View logs
show-logs:
	docker-compose logs -f backend telegram-bot

stop-backend:
	kill -9 $(lsof -ti:8000) || true

show-processes:
	@echo "=== Python Processes ==="
	@ps aux | grep -v grep | grep "python" || true
	@echo "\n=== Node Processes ==="
	@ps aux | grep -v grep | grep "node" || true
	@echo "\n=== Uvicorn Processes ==="
	@ps aux | grep -v grep | grep "uvicorn" || true
	@echo "\n=== Telegram/Bot Processes ==="
	@ps aux | grep -v grep | grep -E "telegram|bot|tg_" || true
	@echo "\n=== Port Usage ==="
	@echo "Port 8000 (Backend):"
	@lsof -i :8000 || true
	@echo "\nPort 3000 (Frontend):"
	@lsof -i :3000 || true
