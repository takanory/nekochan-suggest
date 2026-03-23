# クイックスタート: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**Feature**: `003-emoji-query`  
**Date**: 2026-03-22

---

## 前提条件

1. **Ollama がインストール・起動済みであること**

   ```bash
   # Ollama の起動確認
   curl http://localhost:11434/api/tags
   ```

2. **埋め込みモデルが取得済みであること**

   ```bash
   ollama pull nomic-embed-text
   ```

3. **アノテーションファイルが生成済みであること**

   ```bash
   nekochan-suggest build-annotations
   # → ~/.local/share/nekochan-suggest/annotations.json が生成される
   ```

4. **`ollama` PyPI パッケージが追加されていること**

   ```bash
   uv add ollama
   ```

---

## 基本的な使い方

### テキスト引数で呼び出す

```bash
nekochan-suggest "今日もいい天気ですね"
```

出力例:

```
1. hare-nya   0.87
2. niko-nya   0.82
3. yatta-nya  0.79
```

### 標準入力から渡す

```bash
echo "あーもう疲れた…" | nekochan-suggest
```

### 候補数を変更する

```bash
nekochan-suggest --count 5 "おはよう"
```

### JSON 形式で出力する

```bash
nekochan-suggest --json "眠い"
```

出力例:

```json
{"suggestions": [{"name": "nemui-nya", "score": 0.9123456}, {"name": "kyukei-nya", "score": 0.8534567}, {"name": "yurui-nya", "score": 0.8012345}]}
```

---

## オプション一覧

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `--count N` | `-n N` | `3` | 候補数（1〜10） |
| `--json` | — | — | JSON 形式で出力 |
| `--timeout N` | — | `30` | タイムアウト秒数 |

---

## 設定のカスタマイズ

設定ファイル `~/.config/nekochan-suggest/config.toml` を作成することで
デフォルト値を変更できる:

```toml
ollama_url = "http://localhost:11434"
embed_model = "nomic-embed-text"
llm_model = "qwen3.5"
timeout = 60
```

環境変数でも設定可能（環境変数が設定ファイルより優先される）:

```bash
export NEKOCHAN_OLLAMA_URL="http://localhost:11434"
export NEKOCHAN_EMBED_MODEL="nomic-embed-text"
export NEKOCHAN_TIMEOUT=60
```

CLI オプションはすべての設定より優先される:

```bash
nekochan-suggest --timeout 120 "重要な処理"
```

---

## Python ライブラリとして使う

```python
from nekochan_suggest.query import suggest

results = suggest("今日のランチ最高だった！", count=3, timeout=30)
for r in results:
    print(f"{r.name}: {r.score:.4f}")
```

---

## エラーのトラブルシューティング

| エラーメッセージ | 原因 | 対処法 |
|----------------|------|--------|
| `annotations file not found` | アノテーションファイルが未生成 | `nekochan-suggest build-annotations` を実行 |
| `cannot connect to Ollama` | Ollama サーバーが起動していない | `ollama serve` を実行 |
| `unexpected response from Ollama` | 埋め込みモデルが未取得 | `ollama pull nomic-embed-text` を実行 |
| `request timed out` | Ollama の応答が遅い | `--timeout` を大きくするか Ollama の状態を確認 |
| `text is empty` | 空文字列を渡した | 1 文字以上のテキストを指定 |
| `text is too long` | 1000 文字超のテキスト | 1000 文字以内に収める |
| `--count must be between 1 and 10` | count が範囲外 | 1〜10 の整数を指定 |

---

## 開発者向けセットアップ

```bash
# リポジトリのクローンと依存関係のインストール
git clone <repo>
cd nekochan-suggest
uv sync

# テストの実行（Ollama 不要）
uv run pytest tests/

# カバレッジ付きテスト
uv run pytest --cov=nekochan_suggest tests/

# 型チェック
uv run pyrefly check nekochan_suggest/

# リント・フォーマット
uv run ruff check . && uv run ruff format --check .
```
