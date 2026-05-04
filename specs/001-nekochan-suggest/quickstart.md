# クイックスタート: nekochan-suggest build-annotations

**フィーチャー**: `001-nekochan-suggest`  
**日付**: 2026-05-04

---

## 前提条件

1. Python 3.13+ と `uv` がインストール済み
2. [Ollama](https://ollama.ai/) がインストール済みで起動中
3. `qwen3.5:2b` モデルが取得済み

```bash
# Ollama モデルの取得（初回のみ）
ollama pull qwen3.5:2b
```

---

## インストール

```bash
# リポジトリのクローンと依存関係のインストール
git clone https://github.com/takanory/nekochan-suggest.git
cd nekochan-suggest
uv sync
```

---

## アノテーションデータベースの構築

```bash
# 全絵文字（PNG のみ、GIF はスキップ）のアノテーションを生成・保存する
# インターネット接続と Ollama の起動が必要
uv run nekochan-suggest build-annotations
```

**出力例**:
```
[1/378] yatta-nya
[2/378] nemui-nya
...
[378/378] haniwa-nya-spin

Skipped 12 GIF emojis (not supported by multimodal model): spin-nya, ...
```

---

## ドライランで動作確認

```bash
# 先頭 3 件のアノテーションをプレビュー（ファイル保存なし）
uv run nekochan-suggest build-annotations --dry-run
```

**出力例（stdout）**:
```json
{"name": "yatta-nya", "annotation": "A cat celebrating with joy...", "embedding": [...], "image_base64": "...", "image_mimetype": "image/png"}
{"name": "nemui-nya", "annotation": "A sleepy cat...", "embedding": [...], ...}
{"name": "niko-nya", "annotation": "A smiling cat...", "embedding": [...], ...}
```

---

## タイムアウトの変更

```bash
# Ollama のレスポンス待ち時間を 60 秒に設定
uv run nekochan-suggest build-annotations --timeout 60
```

---

## 設定ファイル（オプション）

`~/.config/nekochan-suggest/config.toml` を作成して設定をカスタマイズできます:

```toml
llm_model = "qwen3.5:2b"
embed_model = "intfloat/multilingual-e5-base"
ollama_url = "http://localhost:11434"
timeout = "30"
```

または環境変数で上書き可能:

```bash
export NEKOCHAN_LLM_MODEL="qwen3.5:2b"
export NEKOCHAN_OLLAMA_URL="http://localhost:11434"
export NEKOCHAN_TIMEOUT="60"
uv run nekochan-suggest build-annotations
```

---

## 保存先

アノテーションファイルは以下に保存されます:

```
~/.local/share/nekochan-suggest/annotations.json
```

---

## 再実行（中断からの再開）

既存エントリは自動的にスキップされます。中断後に再実行するだけで再開できます:

```bash
# 未処理の絵文字のみ処理される
uv run nekochan-suggest build-annotations
```

---

## テスト実行

```bash
# ユニットテスト（Ollama 不要、モックで動作）
uv run pytest tests/test_annotations.py -v

# カバレッジ付き全テスト
uv run pytest --cov=nekochan_suggest --cov-report=term-missing -m "not integration"
```
