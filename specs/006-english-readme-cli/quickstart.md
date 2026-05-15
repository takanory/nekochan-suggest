# Quickstart: English README and CLI Localization

**Feature**: 006-english-readme-cli  
**Date**: 2026-05-15

---

## 変更内容の確認手順

### 1. CLI ヘルプ文字列の確認

```bash
# テキストクエリのヘルプ（英語であることを確認）
uv run nekochan-suggest --help

# build-annotations のヘルプ（英語であることを確認）
uv run nekochan-suggest build-annotations --help
```

期待する出力例（`--help`）:
```
usage: nekochan-suggest [-h] [--count N] [--json] [TEXT]

Suggest nekochan emoji filenames for a given text.
...
  TEXT        Text to suggest emojis for. Reads from stdin if omitted.
  --count N   Number of suggestions to return (1-10). Default: 3.
  --json      Output results in JSON format to stdout.
```

### 2. README ファイルの確認

```bash
# README.md に日本語文字が含まれていないことを確認
grep -P '[\x{3000}-\x{9FFF}]' README.md && echo "日本語あり" || echo "英語のみ OK"

# README.ja.md が存在することを確認
ls README.ja.md

# README.md の先頭10行に README.ja.md へのリンクがあることを確認
head -10 README.md | grep "README.ja.md"
```

### 3. pyproject.toml の確認

```bash
# description フィールドが英語であることを確認
grep 'description' pyproject.toml
# 期待値: description = "CLI tool to suggest nekochan emoji filenames for a given text."
```

### 4. テストの実行

```bash
# 既存テストがすべてパスすることを確認
uv run pytest tests/ -v
```

---

## 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `README.md` | 全面書き換え | 英語・5セクション・`README.ja.md` へのリンク |
| `README.ja.md` | 新規作成 | 日本語・最新実装反映・5セクション |
| `nekochan_suggest/cli.py` | 文字列変更 | argparse 文字列 7 箇所を英語化 |
| `pyproject.toml` | フィールド変更 | `description` フィールドのみ英語化 |

---

## 実装メモ

### cli.py の変更箇所（7 箇所）

```python
# _build_query_parser() の description
description="Suggest nekochan emoji filenames for a given text."

# text 引数の help
help="Text to suggest emojis for. Reads from stdin if omitted."

# --count の help
help="Number of suggestions to return (1-10). Default: 3."

# --json の help
help="Output results in JSON format to stdout."

# _build_build_annotations_parser() の description
description="Generate and save annotations for all emojis."

# --dry-run の help
help="Preview the first 3 annotations without saving to file."

# --timeout の help
help="HTTP timeout in seconds. Overrides config file and environment variable."
```

### README.md 冒頭（英語リンク）

```markdown
# nekochan-suggest

> For Japanese documentation, see [README.ja.md](README.ja.md).
```
