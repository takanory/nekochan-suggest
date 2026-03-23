# nekochan-suggest Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-22

## Active Technologies
- Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが + `ollama` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装） (003-emoji-query)
- `~/.local/share/nekochan-suggest/annotations.json`（読み取り専用）、 (003-emoji-query)

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
- 003-emoji-query: Added Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが + `ollama` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装）

- 002-project-init: Added Python 3.11+（`tomllib` 標準搭載の最低バージョン。憲法は 3.13+ を指定するが、 + なし（コアは標準ライブラリのみ）。開発依存: `pytest`, `ruff`, `pyrefly`。

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
