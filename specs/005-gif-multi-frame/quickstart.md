# Quickstart: GIF Multi-Frame Annotation Generation

**Feature**: `005-gif-multi-frame`  
**Date**: 2026-05-08

---

## 前提条件

- Python 3.13+、uv がインストール済み
- Ollama がローカルで起動中（デフォルト: `http://localhost:11434`）
- `gemma4:e4b`（または別のビジョン対応モデル）が Ollama にプル済み

```bash
ollama pull gemma4:e4b
```

---

## インストール

```bash
# 依存関係インストール（Pillow が core deps に追加されているため自動インストール）
uv sync
```

---

## 基本的な使い方

### アノテーション生成（デフォルト: 最大 4 フレーム）

```bash
# 全絵文字のアノテーションを生成（GIF は最大 4 フレームを LLM に渡す）
nekochan-suggest build-annotations

# プレビューのみ（ファイルに書き込まない）
nekochan-suggest build-annotations --dry-run
```

### フレーム数を変更する

```bash
# GIF 1 件あたり最大 2 フレームに制限（高速・低トークン消費）
NEKOCHAN_GIF_MAX_FRAMES=2 nekochan-suggest build-annotations

# GIF 1 件あたり最大 8 フレームに拡張（高品質・処理時間増）
NEKOCHAN_GIF_MAX_FRAMES=8 nekochan-suggest build-annotations
```

### 設定ファイルで永続的に設定する

`~/.config/nekochan-suggest/config.toml`:
```toml
gif_max_frames = 4
```

### ログレベルを DEBUG に設定してフレーム抽出を確認する

```bash
NEKOCHAN_LOG_LEVEL=DEBUG nekochan-suggest build-annotations --dry-run 2>&1 | grep "Extracted"
# 出力例: DEBUG: Extracted 4 frames from gif: neko_wave.gif
```

---

## 動作確認

```bash
# テストを実行して実装を検証
uv run pytest tests/test_annotations.py -v

# 型チェック
uv run pyrefly nekochan_suggest/

# リントとフォーマットチェック
uv run ruff check . && uv run ruff format --check .
```

---

## 注意事項

- 既存の GIF アノテーション（1 フレーム方式で生成済み）は、マルチフレーム方式で上書き再生成される。
- `NEKOCHAN_GIF_MAX_FRAMES=0` または負の値を指定した場合、WARNING ログを出してデフォルト（4）を使用する。
- `annotations.json` に保存される `image_base64` は元の GIF データのまま（変換フレームは保存しない）。
