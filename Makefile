.PHONY: lint format typecheck test check

## lint: ruff でリンティング（エラーのみ、ファイル変更なし）
lint:
	uv run ruff check .

## format: ruff でフォーマット（ファイル変更あり / CI では ruff format --check . を推奨）
format:
	uv run ruff format .

## typecheck: pyrefly で型検査
typecheck:
	uv run pyrefly check

## test: pytest で全テストを実行
test:
	uv run pytest

## check: lint・typecheck・test をすべて実行（CI 用）
check: lint typecheck test
