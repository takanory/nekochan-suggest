# CLI Contract: nekochan-suggest (English)

**Feature**: 006-english-readme-cli  
**Date**: 2026-05-15  
**Status**: Updated — argparse 文字列を英語化した後の正式仕様

---

## コマンド: `nekochan-suggest`

### Synopsis

```
nekochan-suggest [OPTIONS] [TEXT]
nekochan-suggest build-annotations [OPTIONS]
```

---

## サブコマンド 1: テキストクエリ（デフォルト）

```
usage: nekochan-suggest [-h] [--count N] [--json] [TEXT]

Suggest nekochan emoji filenames for a given text.

positional arguments:
  TEXT           Text to suggest emojis for. Reads from stdin if omitted.

options:
  -h, --help     show this help message and exit
  --count N, -n N
                 Number of suggestions to return (1-10). Default: 3.
  --json         Output results in JSON format to stdout.
```

### 終了コード

| コード | 意味 |
|--------|------|
| `0` | 正常終了 |
| `1` | バリデーションエラー / アノテーションファイル不在 / 埋め込みエラー |

### 出力形式（テキスト）

```
1. yatta-nya  0.87
2. niko-nya  0.82
3. nemui-nya  0.79
```

### 出力形式（`--json`）

```json
{
  "suggestions": [
    {"name": "yatta-nya", "score": 0.8734567},
    {"name": "niko-nya", "score": 0.8213456}
  ]
}
```

---

## サブコマンド 2: `build-annotations`

```
usage: nekochan-suggest build-annotations [-h] [--dry-run] [--timeout SECONDS]

Generate and save annotations for all emojis.

options:
  -h, --help           show this help message and exit
  --dry-run            Preview the first 3 annotations without saving to file.
  --timeout SECONDS, -t SECONDS
                       HTTP timeout in seconds. Overrides config file and
                       environment variable.
```

### 終了コード

| コード | 意味 |
|--------|------|
| `0` | 正常終了 |
| `1` | aliases.json 取得失敗 / Ollama 接続失敗 |

### stderr 出力形式（進行表示）

```
[42/256] happy-nya
```

### stderr 出力形式（スキップ通知）

```
Skipped 3 emojis due to errors: broken-gif, bad-png, timeout-nya
```

---

## エラーメッセージ一覧（英語固定）

| 状況 | メッセージ | ストリーム |
|------|-----------|-----------|
| テキストが空 | `Error: text is empty.` | stderr |
| テキスト長超過 | `Error: text is too long (max 1000 characters).` | stderr |
| `--count` 範囲外 | `Error: --count out of range (1-10).` | stderr |
| TTY かつ TEXT 未指定 | `Error: provide text as an argument or pipe it via stdin.` | stderr |
| アノテーションファイル不在 | `Error: annotations file not found. Run 'nekochan-suggest build-annotations' first.` | stderr |
| 埋め込みモデルロード失敗 | `Error: failed to load embedding model '{model}'.` | stderr |
| 埋め込み失敗 | `Error: embedding failed: {reason}` | stderr |
| 埋め込み結果不正 | `Error: unexpected embedding result. Check embed_model setting.` | stderr |
| aliases.json 取得失敗 | `Error: failed to fetch aliases.json: {reason}` | stderr |
| Ollama 接続失敗 | `Error: failed to connect to Ollama at {url}. Is Ollama running?` | stderr |
