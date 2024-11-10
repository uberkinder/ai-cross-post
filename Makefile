.PHONY: run-all run-backend run-frontend db-reset db-open db-show-tables db-show-schema db-query db-init kill-backend kill-frontend show-logs stop-backend

# Переменные
PYTHON = python
DB_PATH = backend/db/app.db

# Запуск сервисов
run-all:
	make run-backend & make run-frontend

run-backend:
	cd backend && python -m uvicorn app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm start

# Команды для остановки сервисов
kill-backend:
	@for port in 8000 8001 8002; do \
		if lsof -ti :$$port > /dev/null; then \
			echo "Killing process on port $$port"; \
			kill -9 $$(lsof -ti:$$port) || true; \
		fi \
	done
	@if pgrep -f "telegram bot" > /dev/null; then \
		pkill -f "telegram bot"; \
		echo "Telegram bot stopped"; \
	else \
		echo "Telegram bot is not running"; \
	fi

kill-frontend:
	@if lsof -i :3000 > /dev/null; then \
		kill $$(lsof -t -i:3000); \
		echo "Frontend server stopped"; \
	else \
		echo "Frontend server is not running"; \
	fi

# Команды для работы с базой данных
db-reset:
	cd backend && $(PYTHON) -c "from app.services.db_service import DatabaseService; DatabaseService().reset_db()"
	@echo "Database has been reset successfully!"

db-init:
	cd backend && $(PYTHON) -c "from app.services.db_service import DatabaseService; DatabaseService()"
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

# Тесты
test-backend:
	cd backend && $(PYTHON) -m pytest

# Просмотр логов
show-logs:
	@if [ -f backend/logs/app.log ]; then \
		tail -f backend/logs/app.log; \
	else \
		echo "Log file not found at backend/logs/app.log"; \
		exit 1; \
	fi

# Примеры использования:
# make db-query q="SELECT * FROM telegram_bindings;"
# make db-query q="SELECT * FROM telegram_channels;"

stop-backend:
	kill -9 $(lsof -ti:8000) || true