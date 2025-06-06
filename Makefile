# 🛠 AutoClose Makefile - Dev Tools

RENDER_API_TOKEN := $(shell grep RENDER_API_TOKEN .env | cut -d '=' -f2)
RENDER_SERVICE_ID := $(shell grep RENDER_SERVICE_ID .env | cut -d '=' -f2)

.PHONY: format lint types test check all deploy logs logs-render types-fix style

format:
	@echo "🧹 Formatting code with Black..."
	@black .

lint:
	@echo "🧼 Checking code formatting with Black..."
	@black --check . || (echo '❌ Code not formatted. Run `make format` to fix.' && exit 1)

types:
	@echo "🔎 Checking type hints with mypy..."
	@echo "🔧 Installing missing type stubs..." && mypy --install-types --non-interactive > /dev/null || true
	@mypy --config-file mypy.ini utils/ routes/ app.py test_report_utils.py || (echo '❌ Type check failed.' && exit 1)

test:
	@echo "🔍 Running tests with pytest..."
	@pytest test_report_utils.py -v || (echo '❌ Tests failed.' && exit 1)

style:
	@echo "🎨 Checking style with flake8..."
	@flake8 . || (echo '❌ Style check failed. Run `flake8 .` to see details.' && exit 1)

check: lint types style test
	@echo "✅ All checks passed."

all: format check

deploy: check
	@echo "🚀 Deploying to GitHub and triggering Render..."
	@git add .
	@git commit -m "🚀 AutoDeploy: $(shell date +'%Y-%m-%d %H:%M:%S')" || echo "ℹ️ No changes to commit."
	@git push origin main
	@echo "✅ Code pushed to GitHub. Render will pick up the changes."

logs:
	@if [ -f .env ]; then \
		echo "📜 Extracting last commit info..."; \
		git log -1 --pretty=format:"🧾 %h - %s (%cr) by %an"; \
	else \
		echo "❌ .env not found. Can't extract token or context."; \
	fi

logs-render:
	@echo "📡 Fetching latest logs from Render for service: $(RENDER_SERVICE_ID)"
	@curl -s -H "Authorization: Bearer $(RENDER_API_TOKEN)" \
	"https://api.render.com/v1/services/$(RENDER_SERVICE_ID)/deploys?limit=1" \
	| jq -r '.[] | "🧾 Status: \(.status)\n🕒 Created: \(.createdAt)\n📦 Commit: \(.commit.message)\n🔗 Logs:\nhttps://dashboard.render.com/web/services/$(ENV:RENDER_SERVICE_ID)/deploys/\(.id)"'

types-fix:
	@echo "🔧 Installing missing type stubs..."
	@pip install --quiet pandas-stubs types-Pillow types-requests || true
	@echo "📦 Running mypy auto-type install..."
	@mypy --install-types --non-interactive || true
	@echo "📁 Ensuring __init__.py exists in routes/"
	@touch routes/__init__.py
	@echo "🔁 Re-running type check..."
	@mypy utils/ routes/ app.py test_report_utils.py || (echo '❌ Type check failed.' && exit 1)
