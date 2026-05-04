# データモデル: ネコチャン絵文字アノテーション構築コマンド（build-annotations）

**フィーチャー**: `001-nekochan-suggest`  
**日付**: 2026-05-04

---

## エンティティ

### AnnotationRecord（アノテーションレコード）

`~/.local/share/nekochan-suggest/annotations.json` に保存される 1 件のレコード。

| フィールド | 型 | 説明 | バリデーション |
|-----------|------|------|--------------|
| `name` | `str` | 絵文字ファイル名（`-nya` 付き、拡張子なし） | 空文字列不可、例: `yatta-nya` |
| `annotation` | `str` | LLM 生成の英語アノテーション（2〜3文） | 空文字列不可 |
| `embedding` | `list[float]` | `"passage: {annotation}"` から生成した埋め込みベクトル | 長さ固定（モデル依存） |
| `image_base64` | `str` | 絵文字画像の base64 文字列（PNG のみ、GIF は空文字列） | — |
| `image_mimetype` | `str` | 画像の MIME タイプ（例: `image/png`） | — |

**JSON サンプル**:
```json
{
  "name": "yatta-nya",
  "annotation": "A cat celebrating with joy. Use when expressing success, achievement, or excitement. Conveys a positive and energetic mood.",
  "embedding": [0.0123, -0.0456, ...],
  "image_base64": "iVBORw0KGgoAAAA...",
  "image_mimetype": "image/png"
}
```

---

### 外部データソース（読み取り専用）

#### aliases.json（GitHub Raw）

**URL**: `https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/aliases.json`

```json
{
  "yatta-nya": ["yatta"],
  "nemui-nya": ["nemui", "sleepy"],
  "haniwa-nya-spin": []
}
```

| フィールド | 型 | 説明 |
|-----------|------|------|
| キー | `str` | 絵文字ファイル名（`-nya` 付き） |
| 値 | `list[str]` | エイリアスのリスト（空リスト可） |

#### nekochan_emoji.json（GitHub Raw）

**URL**: `https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/nekochan_emoji.json`

```json
{
  "yatta-nya": {
    "aliases": ["yatta"],
    "base64": "iVBORw0KGgoAAAA...",
    "mimetype": "image/png"
  },
  "spin-nya": {
    "aliases": ["spin"],
    "base64": "R0lGODlh...",
    "mimetype": "image/gif"
  }
}
```

| フィールド | 型 | 説明 |
|-----------|------|------|
| キー | `str` | 絵文字ファイル名（`-nya` 付き） |
| `aliases` | `list[str]` | エイリアスのリスト |
| `base64` | `str` | 画像の base64 文字列 |
| `mimetype` | `str` | `image/png` または `image/gif` |

---

## 状態遷移

### `build_all_annotations()` の絵文字処理フロー

```
[aliases.json 取得] → [nekochan_emoji.json 取得]
      ↓
[各絵文字をループ]
      ↓
  既存エントリ? → YES → スキップ（再開ロジック）
      ↓ NO
  mimetype == image/gif? → YES → skipped_gif に追加 → continue
      ↓ NO
  generate_annotation() → 失敗? → YES → skipped に追加 → continue
      ↓ OK
  generate_embedding()
      ↓
  save_annotations_file()（全件上書き）
      ↓
[完了後: skipped_gif / skipped を stderr に報告]
```

---

## バリデーションルール

| ルール | 適用箇所 |
|-------|---------|
| HTTP 非 200 → `ValueError` | `fetch_aliases()`, `fetch_emoji_data()` |
| `OSError` → `ValueError` にラップ（aliases のみ） | `build_all_annotations()` |
| `mimetype == "image/gif"` → スキップ | `build_all_annotations()` |
| LLM/埋め込みエラー → スキップ（`skipped` リスト） | `build_all_annotations()` |
| dry-run 時は 3 件プレビュー後に break | `build_all_annotations()` |

---

## 設定キー（`config` 辞書）

`_load_config()` が返す `dict[str, str]` のキー一覧（`build_all_annotations` が使用するもの）:

| キー | デフォルト | 環境変数 | 設定ファイルキー |
|-----|---------|---------|----------------|
| `ollama_url` | `http://localhost:11434` | `NEKOCHAN_OLLAMA_URL` | `ollama_url` |
| `llm_model` | `qwen3.5:2b` | `NEKOCHAN_LLM_MODEL` | `llm_model` |
| `embed_model` | `intfloat/multilingual-e5-base` | `NEKOCHAN_EMBED_MODEL` | `embed_model` |
| `timeout` | `30` | `NEKOCHAN_TIMEOUT` | `timeout` |
