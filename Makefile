.PHONY: dev test build deploy bootstrap

# Development commands
.PHONY: dev setup test-api full-setup deploy-ec2 manage-ec2 setup-domain setup-dns setup-nginx setup-ssl start-prod deploy-prod
dev: ## Start development server
	poetry run uvicorn src.a3e.main:app --host 0.0.0.0 --port 8000 --reload

start-prod: ## Start production server with Gunicorn
	./scripts/start_production.sh

deploy-prod: ## Full production deployment (run on server)
	sudo ./scripts/deploy_production.sh

setup: ## Setup development environment
	poetry install
	docker-compose up -d postgres milvus redis
	sleep 10
	$(MAKE) init-db
	poetry run alembic upgrade head

test-api: ## Test API endpoints
	poetry run python scripts/test_api.py

full-setup: ## Complete system setup with testing
	./scripts/setup_system.py

deploy-ec2: ## Deploy to EC2 instance
	./scripts/deploy_ec2.sh

manage-ec2: ## Manage EC2 deployment (usage: make manage-ec2 COMMAND=status)
	./scripts/manage_ec2.sh $(COMMAND)

setup-domain: ## Complete domain setup (NGINX + SSL for api.mapmystandards.ai)
	./scripts/setup_domain.sh

setup-dns: ## DNS configuration instructions for Namecheap
	chmod +x scripts/setup_dns.sh
	./scripts/setup_dns.sh

setup-nginx: ## Configure NGINX reverse proxy
	./scripts/setup_nginx.sh

setup-ssl: ## Setup SSL certificate with Let's Encrypt
	./scripts/setup_ssl.sh

test: ## Run tests
	poetry run pytest -v --cov=src/a3e --cov-report=html

build: ## Build Docker image
	docker build -t a3e:latest .

logs: ## Show logs
	docker-compose logs -f

stop: ## Stop all services
	docker-compose down

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

bootstrap: ## Bootstrap production environment
	@echo "🏗️ Bootstrapping A3E production environment..."
	terraform -chdir=infra init
	terraform -chdir=infra apply -auto-approve
	./scripts/deploy.sh

seed: ## Seed development data
	poetry run python scripts/seed_data.py

lint: ## Run linting
	poetry run black src/ tests/
	poetry run isort src/ tests/
	poetry run flake8 src/ tests/
	poetry run mypy src/

install: ## Install dependencies
	poetry install
	poetry run pre-commit install

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
