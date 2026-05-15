# nekochan-suggest Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-15

## Active Technologies
- Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが + `ollama` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装） (003-emoji-query)
- `~/.local/share/nekochan-suggest/annotations.json`（読み取り専用）、 (003-emoji-query)
- Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが + `sentence-transformers` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装） (003-emoji-query)
- Python 3.13+（`uv` 管理、`.venv` 使用） + `streamlit>=1.57.0`（optional `[gui]` extra）、既存: `sentence-transformers` (004-streamlit-ui)
- `~/.local/share/nekochan-suggest/annotations.json`（読み取りのみ） (004-streamlit-ui)
- Python 3.14.2（`uv` 管理、`.venv`） + Pillow（GIF フレーム抽出）、Ollama HTTP API（LLM）、sentence-transformers（埋め込み） (005-gif-multi-frame)
- `~/.local/share/nekochan-suggest/annotations.json`（JSON ファイル） (005-gif-multi-frame)
- Python 3.13+ + `argparse`（標準ライブラリ）— 新規依存なし (006-english-readme-cli)
- N/A（コード・ドキュメントの文字列変更のみ） (006-english-readme-cli)

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
- 006-english-readme-cli: Added Python 3.13+ + `argparse`（標準ライブラリ）— 新規依存なし
- 005-gif-multi-frame: Added Python 3.14.2（`uv` 管理、`.venv`） + Pillow（GIF フレーム抽出）、Ollama HTTP API（LLM）、sentence-transformers（埋め込み）
- 004-streamlit-ui: Added Python 3.13+（`uv` 管理、`.venv` 使用） + `streamlit>=1.57.0`（optional `[gui]` extra）、既存: `sentence-transformers`


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
