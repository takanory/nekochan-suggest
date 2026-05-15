# Data Model: English README and CLI Localization

**Feature**: 006-english-readme-cli  
**Date**: 2026-05-15

## 概要

本フィーチャーはコードロジックの変更を行わないため、新規エンティティ・
データ構造の追加はない。影響を受ける「データ」は文字列リテラルのみ。

---

## 変更対象文字列マッピング

### `nekochan_suggest/cli.py`

| 場所 | フィールド | 変更前（日本語） | 変更後（英語） |
|------|-----------|----------------|---------------|
| `_build_query_parser()` | `description` | `文章に対してネコチャン絵文字のファイル名を提案するツール。` | `Suggest nekochan emoji filenames for a given text.` |
| `text` 引数 | `help` | `絵文字提案を求めるテキスト。省略時は標準入力から読み取る。` | `Text to suggest emojis for. Reads from stdin if omitted.` |
| `--count` / `-n` | `help` | `返す候補数（1〜10）。デフォルト: 3。` | `Number of suggestions to return (1-10). Default: 3.` |
| `--json` | `help` | `結果をJSON形式で標準出力に出力する。` | `Output results in JSON format to stdout.` |
| `_build_build_annotations_parser()` | `description` | `全絵文字のアノテーションを生成・保存する。` | `Generate and save annotations for all emojis.` |
| `--dry-run` | `help` | `ファイルを保存せず、先頭3件のアノテーションをプレビュー表示する。` | `Preview the first 3 annotations without saving to file.` |
| `--timeout` / `-t` | `help` | `HTTP タイムアウト秒数。設定ファイル・環境変数より優先される。` | `HTTP timeout in seconds. Overrides config file and environment variable.` |

### `pyproject.toml`

| フィールド | 変更前 | 変更後 |
|-----------|--------|--------|
| `[project].description` | `文章に対してネコチャン絵文字を提案するCLIツール` | `CLI tool to suggest nekochan emoji filenames for a given text.` |

### ドキュメントファイル

| ファイル | 操作 | 内容 |
|---------|------|------|
| `README.md` | 全面書き換え | 英語 5 セクション構成（概要・インストール・使い方・開発・ライセンス） |
| `README.ja.md` | 新規作成 | 日本語 5 セクション構成（最新実装反映） |

---

## 不変事項

以下は本フィーチャーの対象外であり変更しない:

- `nekochan_suggest/cli.py` の docstring・コメント（日本語のまま）
- `nekochan_suggest/annotations.py` の logging メッセージ（日本語のまま可）
- `nekochan_suggest/ui.py`（Streamlit UI、対象外）
- `pyproject.toml` の description 以外のフィールド・コメント
- `tests/` の docstring・コメント
