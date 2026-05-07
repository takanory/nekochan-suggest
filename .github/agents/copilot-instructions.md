# nekochan-suggest Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-04

## Active Technologies
- Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが + `ollama` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装） (003-emoji-query)
- `~/.local/share/nekochan-suggest/annotations.json`（読み取り専用）、 (003-emoji-query)
- Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが + `sentence-transformers` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装） (003-emoji-query)
- Python 3.13+（`uv` 管理、`.venv` 使用） + `streamlit>=1.57.0`（optional `[gui]` extra）、既存: `sentence-transformers` (004-streamlit-ui)
- `~/.local/share/nekochan-suggest/annotations.json`（読み取りのみ） (004-streamlit-ui)

- Python 3.11+（`tomllib` 標準搭載の最低バージョン。憲法は 3.13+ を指定するが、 + なし（コアは標準ライブラリのみ）。開発依存: `pytest`, `ruff`, `pyrefly`。 (002-project-init)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+（`tomllib` 標準搭載の最低バージョン。憲法は 3.13+ を指定するが、: Follow standard conventions

## Recent Changes
- 004-streamlit-ui: Added Python 3.13+（`uv` 管理、`.venv` 使用） + `streamlit>=1.57.0`（optional `[gui]` extra）、既存: `sentence-transformers`
- 004-streamlit-ui: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
- 003-emoji-query: Added Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが + `sentence-transformers` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装）


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
