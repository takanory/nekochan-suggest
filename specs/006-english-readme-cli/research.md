# Research: English README and CLI Localization

**Feature**: 006-english-readme-cli  
**Date**: 2026-05-15  
**Status**: Complete — 調査対象の不明点なし

## 調査概要

本フィーチャーには外部技術の選定・設計判断がなく、既存コードの文字列置き換えのみ。
調査の主目的は「現状のコード・ドキュメントのどこに日本語文字列が存在するか」の
棚卸しと、README の構成方針の確認。

---

## 調査 1: 変更対象文字列の棚卸し

### 決定事項
変更が必要なファイルと箇所を特定した。

### 調査結果

#### `nekochan_suggest/cli.py` — argparse 日本語文字列 7 箇所

| 場所 | 現在の日本語文字列 | 英語候補 |
|------|--------------------|----------|
| `_build_query_parser()` description | `"文章に対してネコチャン絵文字のファイル名を提案するツール。"` | `"Suggest nekochan emoji filenames for a given text."` |
| `text` help | `"絵文字提案を求めるテキスト。省略時は標準入力から読み取る。"` | `"Text to suggest emojis for. Reads from stdin if omitted."` |
| `--count` help | `"返す候補数（1〜10）。デフォルト: 3。"` | `"Number of suggestions to return (1-10). Default: 3."` |
| `--json` help | `"結果をJSON形式で標準出力に出力する。"` | `"Output results in JSON format to stdout."` |
| `_build_build_annotations_parser()` description | `"全絵文字のアノテーションを生成・保存する。"` | `"Generate and save annotations for all emojis."` |
| `--dry-run` help | `"ファイルを保存せず、先頭3件のアノテーションをプレビュー表示する。"` | `"Preview the first 3 annotations without saving to file."` |
| `--timeout` help | `"HTTP タイムアウト秒数。設定ファイル・環境変数より優先される。"` | `"HTTP timeout in seconds. Overrides config file and environment variable."` |

#### `pyproject.toml` — description フィールド 1 箇所

| 現在 | 英語候補 |
|------|----------|
| `"文章に対してネコチャン絵文字を提案するCLIツール"` | `"CLI tool to suggest nekochan emoji filenames for a given text."` |

#### `README.md` — 全面書き換え

現在の `README.md` は日本語で書かれており、かつ「未実装スタブ」という古い説明が
残っている（機能 001〜005 はすでに実装済み）。全面的な英語での書き直しが必要。

#### `README.ja.md` — 新規作成

存在しない。最新の実装状態（機能 001〜005 の内容）を反映した日本語版として
新規作成する。現行 `README.md` のテキストをベースにしつつ、古いスタブ説明を
削除して最新状態に更新する。

#### `tests/test_cli.py` — アサーション文字列の更新確認

テスト内の日本語文字列を確認した。テストのアサーション（`assert ... in result.stderr`
等）はほぼすべて英語文字列を使っている。日本語はテストの docstring に残っているが
それは対象外。

CLI argparse 文字列変更の影響を受けるテスト:
- `test_cli_help_contains_options` — `--count`, `--json` の存在確認のみ（文字列変更無影響）
- `test_handle_query_validation_errors` — エラーメッセージは英語のまま（変更不要）

**結論**: `tests/test_cli.py` に日本語アサーション文字列はなく、更新不要。
SC-005 は argparse ヘルプ文字列変更後も `pytest` がパスするかの確認で充足できる。

---

## 調査 2: README 構成方針

### 決定事項
- **Decision**: `README.md` はプロジェクト概要・インストール・CLI使い方・開発・ライセンスの
  5セクション構成とする。`README.ja.md` へのリンクはタイトル直下に配置。
- **Rationale**: 国際標準の OSS README 構成に準拠。日本語ユーザーへの配慮として
  先頭にリンクを置く。
- **Alternatives considered**: バッジで案内する案 → テキストリンクのほうが視認性高い。

### README.md セクション構成（英語）

```
# nekochan-suggest
> 日本語版は README.ja.md を参照してください

[badges]

## Overview
## Installation
## Usage (CLI)
## Development
## License
```

### README.ja.md セクション構成（日本語・最新実装反映）

```
# nekochan-suggest（日本語）

## 概要
## インストール
## 使い方（CLI）
  - テキストから絵文字を提案
  - --count, --json オプション
  - build-annotations サブコマンド（--dry-run, --timeout）
  - GIF 対応についての補足
## 開発
## ライセンス
```

---

## 調査 3: テスト影響範囲の確認

### 決定事項
- **Decision**: `tests/test_cli.py` の変更は不要。`uv run pytest tests/` が
  argparse 文字列変更後もパスすることを確認してタスクを完了とする。
- **Rationale**: 既存テストのアサーションは英語文字列を直接テストしており、
  argparse の `description`/`help` 文字列の変更では壊れない。
  `test_cli_help_contains_options` は `--count`/`--json` というオプション名のみを
  確認しており、ヘルプテキスト本文は対象外。
- **Alternatives considered**: `--help` 出力の英語キーワードを明示的にテストする
  新規テスト追加 → SC によって「新規テスト追加なし」と決定済みのため却下。

---

## 結論

NEEDS CLARIFICATION なし。すべての技術的不明点は調査により解決した。
Phase 1 設計へ進む。
