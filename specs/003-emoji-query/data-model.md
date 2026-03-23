# データモデル: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**Feature**: `003-emoji-query`  
**Date**: 2026-03-22

---

## エンティティ一覧

### 1. `NekochanEmoji`（アノテーションファイル内の 1 レコード）

アノテーションファイル `~/.local/share/nekochan-suggest/annotations.json` に
保存されている絵文字レコード。**コードで型として定義しない**（JSON を dict として扱う）。

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `name` | `str` | 必須 | 画像ファイル名（例: `yatta-nya`）拡張子なし |
| `annotation` | `str` | 必須 | LLM が生成した英語の説明テキスト |
| `embedding` | `list[float]` | 任意 | annotation から生成した埋め込みベクトル。欠損レコードはスキップ |

**ファイル全体のトップレベル構造**: 配列 `[{...}, ...]`

**バリデーションルール**:
- `embedding` フィールドが欠損しているレコードは処理時にスキップする。
- `embedding` が空配列のレコードもスキップする（コサイン類似度計算不可）。
- その他のフィールド欠損はスキップ扱いとし、エラーを raise しない。

**JSON スキーマ例**:
```json
[
  {
    "name": "yatta-nya",
    "annotation": "A cat jumping with joy and excitement, expressing celebration.",
    "embedding": [0.0231, -0.1456, 0.8723, "...（768 次元）"]
  },
  {
    "name": "nemui-nya",
    "annotation": "A sleepy cat, half-closed eyes, looking tired.",
    "embedding": [...]
  }
]
```

---

### 2. `SuggestionResult`（提案結果の 1 件）

クエリ結果として返す提案 1 件を表す Python `dataclass`。
`query.py` モジュールで定義する。

```python
from dataclasses import dataclass

@dataclass
class SuggestionResult:
    """絵文字提案結果の 1 件。"""
    name: str   # 画像ファイル名（例: yatta-nya）
    score: float  # コサイン類似度スコア（0.0〜1.0）
```

| フィールド | 型 | 説明 |
|------------|-----|------|
| `name` | `str` | 画像ファイル名（拡張子なし） |
| `score` | `float` | コサイン類似度スコア（0.0〜1.0） |

**アクセス方法**: `result.name`, `result.score`  
**出力フォーマット**:
- テキスト: `1. yatta-nya  0.87`（スコア小数点以下 2 桁固定）
- JSON: `{"name": "yatta-nya", "score": 0.8734567}`（スコア丸めなし）

---

### 3. `QueryInput`（概念的入力パラメータ — コード型として実装しない）

`suggest()` 関数に渡す引数の概念的な記述。実際のコードでは個別引数として渡す。

| パラメータ | 型 | デフォルト | バリデーション |
|-----------|-----|-----------|-------------|
| `text` | `str` | — | strip 後に 1 文字以上、1000 文字以下 |
| `count` | `int` | `3` | 1〜10 の整数。0 以下または 11 以上はエラー |
| `timeout` | `int` | `30` | 正の整数（秒） |

**`json_mode`**: `suggest()` には渡さない。CLI 層が処理する。

---

## 状態遷移

クエリ処理のデータフロー:

```
入力テキスト (str)
    └─[バリデーション]─→ ValidatedText
         └─[ollama.embed()]─→ QueryVector (list[float], 768 次元)
              └─[_cosine_similarity() × N件]─→ ScoredList (list[tuple[str, float]])
                   └─[上位 count 件選択]─→ list[SuggestionResult]
```

---

## 設定エンティティ（`AppConfig`）

コード型として定義しないが、設定解決の結果として使用する内部状態。

| キー | env var | config.toml キー | デフォルト値 |
|------|---------|-----------------|------------|
| `ollama_url` | `NEKOCHAN_OLLAMA_URL` | `ollama_url` | `http://localhost:11434` |
| `embed_model` | `NEKOCHAN_EMBED_MODEL` | `embed_model` | `nomic-embed-text` |
| `llm_model` | `NEKOCHAN_LLM_MODEL` | `llm_model` | `qwen3.5` |
| `timeout` | `NEKOCHAN_TIMEOUT` | `timeout` | `30` |

**優先順位**: `--timeout` CLI オプション > 環境変数 > config.toml > デフォルト値

---

## ファイルパス定数

| 定数 | パス |
|------|------|
| `ANNOTATIONS_PATH` | `~/.local/share/nekochan-suggest/annotations.json` |
| `CONFIG_PATH` | `~/.config/nekochan-suggest/config.toml` |

`pathlib.Path.home()` を使用して解決する。
