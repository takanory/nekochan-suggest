# リサーチメモ: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**Feature**: `003-emoji-query`  
**Date**: 2026-03-22  
**Status**: Resolved（NEEDS CLARIFICATION なし）

---

## 1. ollama Python パッケージ API（埋め込み生成）

### 決定事項

`ollama.Client` を使用し、`embed()` メソッド（新 API）で埋め込みを取得する。

```python
import ollama

client = ollama.Client(host=ollama_url, timeout=timeout_seconds)
response = client.embed(model=embed_model, input=text)
vector: list[float] = list(response.embeddings[0])
```

### 理由

- `embed()` は現行推奨 API（`EmbedResponse.embeddings: Sequence[Sequence[float]]` を返す）。
- `embeddings()`（旧 API）は `EmbeddingsResponse.embedding: Sequence[float]` を返すが、
  将来の非推奨化リスクがある。
- `Client(host=..., timeout=...)` の `timeout` は内部 `httpx.Client` に
  `**kwargs` 経由で渡されるため、リクエストタイムアウトとして機能する。

### 検討した代替案

| 案 | 却下理由 |
|----|---------|
| `ollama.embeddings()` (旧 API) | 将来的に非推奨化の可能性がある |
| `urllib` で直接 HTTP 呼び出し | 仕様書でパッケージ使用が明記されている |

### エラーハンドリング

| 例外 | 発生条件 | 対処 |
|------|---------|------|
| `ConnectionError` (Python 組み込み) | Ollama サーバー未起動 / 接続拒否 | `"Error: cannot connect to Ollama ..."` を stderr に出力 |
| `ollama.ResponseError` | HTTP エラー、モデル未取得など | `"Error: Ollama returned an error ..."` を stderr に出力 |
| `httpx.TimeoutException` | タイムアウト発生 | `"Error: request timed out ..."` を stderr に出力 |
| `ValueError`（空 embeddings） | `response.embeddings` が空または形式異常 | `"Error: unexpected response from Ollama ..."` を stderr に出力 |

`httpx.TimeoutException` は `ollama._client._request_raw` でキャッチされないため、
呼び出し元でキャッチする必要がある。

---

## 2. コサイン類似度（純 Python 実装）

### 決定事項

`math` モジュールのみで実装する。numpy や scipy は使用しない。

```python
import math

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)
```

### パフォーマンス見積もり

- `nomic-embed-text` の次元数: 768
- エントリ数: ~378 件
- 1 件あたりの演算: ~2,304 回の浮動小数点演算（ドット積 768 + ノルム計算 768×2）
- 合計: 約 87 万回の浮動小数点演算
- Python での実行時間: 数ミリ秒以内（SC-001 の 1 秒制約を十分に満たす）

### 検討した代替案

| 案 | 却下理由 |
|----|---------|
| `numpy.dot` / `numpy.linalg.norm` | 仕様書で numpy 等の追加 PyPI 依存禁止が明記されている |

---

## 3. 設定ファイル読み込み（`tomllib`）

### 決定事項

Python 3.11+ 標準ライブラリの `tomllib` を使用する。

```python
import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "nekochan-suggest" / "config.toml"

def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)
```

設定値の優先順位（高 → 低）:

1. `--timeout` CLI オプション（timeout のみ）
2. 環境変数（`NEKOCHAN_OLLAMA_URL`, `NEKOCHAN_EMBED_MODEL`, `NEKOCHAN_LLM_MODEL`, `NEKOCHAN_TIMEOUT`）
3. 設定ファイル (`~/.config/nekochan-suggest/config.toml`)
4. デフォルト値

### フラットな TOML 構造

```toml
ollama_url = "http://localhost:11434"
embed_model = "nomic-embed-text"
llm_model = "qwen3.5"
timeout = 30
```

### 検討した代替案

| 案 | 却下理由 |
|----|---------|
| `tomli` (PyPI) | Python 3.11+ では `tomllib` が標準ライブラリに含まれるため不要 |
| JSON 形式 | 仕様書で TOML 形式が明記されている |

---

## 4. 設定解決ロジック

### 決定事項

設定の解決は CLI 層 (`cli.py`) で行い、解決済みの値をライブラリ関数 `suggest()` に渡す。
ただし `ollama_url` と `embed_model` は CLI が直接の引数として受け取らないため、
`query.py` の内部で設定を読み込む。

最終的な責務分担:

| 責務 | 担当モジュール |
|------|--------------|
| `--timeout` CLI 引数の解析 | `cli.py` |
| 環境変数 `NEKOCHAN_TIMEOUT` の読み込みと `--timeout` との優先処理 | `cli.py` |
| `suggest()` に渡す最終 `timeout` 値の決定 | `cli.py` |
| `ollama_url`・`embed_model` の設定読み込み（config + env var） | `query.py` 内部 |

### `NEKOCHAN_TIMEOUT` バリデーション

`NEKOCHAN_TIMEOUT` に整数でない値（例: `"abc"`、`"3.5"`）が設定されていた場合は
`"Error: NEKOCHAN_TIMEOUT must be a positive integer."` を stderr に出力して終了コード 1。

---

## 5. アノテーションファイルの構造とパス

### 決定事項

- **パス**: `~/.local/share/nekochan-suggest/annotations.json`（`pathlib.Path.home()` で解決）
- **トップレベル構造**: 配列 `[{...}, ...]`
- **スキーマ**:
  ```json
  [
    {
      "name": "yatta-nya",
      "annotation": "A cat expressing joy and celebration...",
      "embedding": [0.123, -0.456, ...]
    }
  ]
  ```
- **欠損フィールドの扱い**: `embedding` フィールドが欠損しているレコードはスキップする。

---

## 6. 入力バリデーション

### 決定事項

バリデーションは CLI 層と `suggest()` 両方で行う（防衛的設計）。

| 条件 | エラーメッセージ（英語） | 終了コード |
|------|----------------------|----------|
| text が空（strip 後） | `Error: text is empty.` | 1 |
| text が 1000 文字超 | `Error: text is too long (max 1000 characters).` | 1 |
| `--count` が 0 以下または 11 以上 | `Error: --count must be between 1 and 10.` | 1 |
| アノテーションファイル未存在 | `Error: annotations file not found. Run 'nekochan-suggest build-annotations' first.` | 1 |
| Ollama 接続失敗 | `Error: cannot connect to Ollama at {url}. Make sure Ollama is running.` | 1 |
| Ollama レスポンス異常 | `Error: unexpected response from Ollama. Check if 'ollama pull {model}' was run.` | 1 |
| タイムアウト | `Error: request timed out after {N} seconds.` | 1 |

---

## 7. テキスト出力フォーマット

### 決定事項

| モード | フォーマット例 |
|--------|-------------|
| テキスト（デフォルト） | `1. yatta-nya  0.87` |
| JSON (`--json`) | `{"suggestions": [{"name": "yatta-nya", "score": 0.8734567}]}` |

テキスト出力: `N. <ファイル名>  <スコア>` 形式。スコアは小数点以下 2 桁固定（`f"{score:.2f}"`）。
JSON 出力: スコアは丸めなしの生の浮動小数点。

---

## NEEDS CLARIFICATION 解決状況

すべての不明点は仕様書の明確化セッション（2026-03-22）で解決済み。未解決項目なし。
