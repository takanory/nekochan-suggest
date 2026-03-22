# CLI コントラクト: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**Feature**: `003-emoji-query`  
**Date**: 2026-03-22

---

## コマンド: `nekochan-suggest`（テキストクエリ）

入力テキストに対してネコチャン絵文字のファイル名候補を提案する。

### シグネチャ

```
nekochan-suggest [OPTIONS] [TEXT]
```

### 引数・オプション

| 引数/オプション | 型 | 必須 | デフォルト | 説明 |
|----------------|-----|------|-----------|------|
| `TEXT` | positional | いいえ¹ | — | 提案を求めるテキスト |
| `--count N` / `-n N` | int | いいえ | `3` | 返す候補数（1〜10） |
| `--json` | flag | いいえ | `false` | JSON 形式で出力 |
| `--timeout N` | int | いいえ | `30` | LLM レスポンスのタイムアウト秒数 |

¹ TEXT 省略時は標準入力から読み取る（非 TTY の場合のみ）。TTY の場合は
エラーメッセージを stderr に出力して終了コード 1。

---

## 入力仕様

### テキスト入力

| 入力方法 | 例 |
|---------|------|
| コマンドライン引数 | `nekochan-suggest "今日もいい天気ですね"` |
| 標準入力（パイプ） | `echo "眠い" \| nekochan-suggest` |

### バリデーション

| 条件 | stderr メッセージ | 終了コード |
|------|-----------------|----------|
| text が空（strip 後）| `Error: text is empty.` | 1 |
| text が 1000 文字超 | `Error: text is too long (max 1000 characters).` | 1 |
| `--count` が 0 以下 | `Error: --count must be between 1 and 10.` | 1 |
| `--count` が 11 以上 | `Error: --count must be between 1 and 10.` | 1 |
| `NEKOCHAN_TIMEOUT` が非整数 | `Error: NEKOCHAN_TIMEOUT must be a positive integer.` | 1 |

---

## 出力仕様

### テキスト出力（デフォルト）

書式: `{N}. {ファイル名}  {スコア:.2f}`

```
1. yatta-nya  0.87
2. niko-nya   0.82
3. hare-nya   0.79
```

- 出力先: stdout
- 1 行に 1 候補
- スコアは小数点以下 2 桁固定
- ファイル名とスコアの間はスペース 2 つ

### JSON 出力（`--json` 指定時）

```json
{"suggestions": [{"name": "yatta-nya", "score": 0.8734567}, {"name": "niko-nya", "score": 0.8213456}]}
```

- 出力先: stdout
- 常に有効な JSON
- `score` は丸めなしの浮動小数点（生の値）
- 配列はスコア降順

---

## エラー仕様

すべてのエラーは:
- stderr に英語のメッセージを出力する
- 終了コード 1 で終了する
- stdout には何も出力しない

| エラー条件 | stderr メッセージ |
|-----------|----------------|
| アノテーションファイル未存在 | `Error: annotations file not found. Run 'nekochan-suggest build-annotations' first.` |
| Ollama 接続失敗 | `Error: cannot connect to Ollama at {url}. Make sure Ollama is running.` |
| Ollama レスポンス異常（`embedding` キーなし等） | `Error: unexpected response from Ollama. Check if 'ollama pull {model}' was run.` |
| タイムアウト | `Error: request timed out after {N} seconds.` |
| HTTP エラー | `Error: Ollama returned an error: {message}` |

---

## 環境変数

本コマンドに影響を与える環境変数:

| 変数 | 対応設定キー | デフォルト値 | 説明 |
|------|------------|------------|------|
| `NEKOCHAN_OLLAMA_URL` | `ollama_url` | `http://localhost:11434` | Ollama エンドポイント |
| `NEKOCHAN_EMBED_MODEL` | `embed_model` | `nomic-embed-text` | 埋め込みモデル名 |
| `NEKOCHAN_LLM_MODEL` | `llm_model` | `qwen3.5` | LLM モデル名（build-annotations 用） |
| `NEKOCHAN_TIMEOUT` | `timeout` | `30` | タイムアウト秒数（正の整数のみ） |

**優先順位**: `--timeout` オプション > `NEKOCHAN_TIMEOUT` > `config.toml` > デフォルト値

---

## ライブラリ API コントラクト

CLI を介さずに Python から直接呼び出せる公開 API:

```python
from nekochan_suggest.query import suggest, SuggestionResult

results: list[SuggestionResult] = suggest(
    text="今日もいい天気ですね",
    count=3,
    timeout=30,
)
# result.name: str  — 画像ファイル名
# result.score: float — コサイン類似度（0.0〜1.0）
```

### `suggest()` の事前条件

- `text` は strip 後に 1 文字以上、1000 文字以下
- `count` は 1〜10 の整数
- `timeout` は正の整数（秒）

### `suggest()` の事後条件

- 返り値の長さは `min(count, 利用可能なアノテーション件数)` 以下
- 返り値はスコア降順でソートされている
- `count` がアノテーション件数を超える場合、利用可能な件数をすべて返す（エラーなし）

### 例外

`suggest()` 自体は例外を raise しない。エラーは呼び出し元が `try/except` で捕捉し、
stderr 出力と終了コード 1 の処理を行う（CLI 層の責務）。

> **Note**: 実装では例外を raise する設計も許容する（CLI 層でキャッチ）。
> 最終的な決定はタスク生成フェーズで確定する。

---

## 受け入れシナリオ（契約テスト）

```
シナリオ 1: 正常系（テキスト引数）
  Given: アノテーションファイル存在、Ollama 起動済み
  Input: nekochan-suggest "今日のランチ最高だった！"
  Output: stdout に 3 件の候補（ファイル名 + スコア）
  Exit code: 0

シナリオ 2: JSON 出力
  Given: 同上
  Input: nekochan-suggest --json "おはよう"
  Output: stdout に有効な JSON {"suggestions": [...]}
  Exit code: 0

シナリオ 3: 件数指定
  Given: 同上
  Input: nekochan-suggest --count 5 "おはよう"
  Output: stdout に 5 件の候補
  Exit code: 0

シナリオ 4: 標準入力
  Given: 同上
  Input: echo "眠い" | nekochan-suggest
  Output: stdout に 3 件の候補
  Exit code: 0

シナリオ 5: 空文字列
  Input: nekochan-suggest ""
  Output: stderr に "Error: text is empty."
  Exit code: 1
```
