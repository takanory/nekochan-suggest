# Data Model: GIF Multi-Frame Annotation Generation

**Feature**: `005-gif-multi-frame`  
**Date**: 2026-05-08

---

## エンティティ

### GifFrames（非永続）

アニメーション GIF から抽出した PNG base64 フレームのシーケンス。LLM の `images`
フィールドにリストとして渡すためだけに使用し、`annotations.json` には保存しない。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| frames | `list[str]` | PNG base64 文字列のリスト（N ≤ gif_max_frames） |

**バリデーション**:
- `len(frames) >= 1`（GIF が読めれば必ず1フレーム以上）
- `len(frames) <= gif_max_frames`

---

### AnnotationRecord（変更なし）

`annotations.json` に永続化されるレコード。この機能による変更なし。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| name | `str` | 絵文字ファイル名（拡張子なし） |
| annotation | `str` | LLM が生成した英語アノテーション |
| embedding | `list[float]` | sentence-transformers による埋め込みベクトル |
| image_base64 | `str` | 元画像の base64（GIF の場合は元の GIF データ） |
| image_mimetype | `str` | 元画像の MIME タイプ（GIF の場合は `"image/gif"`） |

**重要**: `image_base64` は変換前の元データを保持する。マルチフレーム PNG 変換後の
データは保存しない（FR-009）。

---

## 設定値

### `_load_config()` への追加

| キー | 型 | デフォルト | 環境変数 | 説明 |
|-----|-----|----------|---------|------|
| `gif_max_frames` | `str`（数値文字列） | `"4"` | `NEKOCHAN_GIF_MAX_FRAMES` | GIF フレームの最大抽出数 |

**バリデーションルール**（`build_all_annotations` で適用）:
- `int(config["gif_max_frames"])` の変換に失敗 → デフォルト 4 を WARNING ログとともに使用
- 変換値 ≤ 0 → デフォルト 4 を WARNING ログとともに使用

---

## 関数シグネチャ（新規・変更）

### `gif_frames_as_png_base64_list`（新規）

```python
def gif_frames_as_png_base64_list(gif_base64: str, max_frames: int) -> list[str]:
    """GIF base64 から複数フレームを PNG base64 リストとして返す。

    max_frames が GIF の総フレーム数を超える場合は全フレームを返す。
    フレームインデックスは均等間隔サンプリング（先頭・末尾を含む）で算出する。

    Args:
        gif_base64: GIF 画像の base64 文字列。
        max_frames: 抽出する最大フレーム数。1 以上でなければならない。

    Returns:
        PNG 変換済みフレームの base64 文字列リスト（長さ: 1 ≤ n ≤ max_frames）。
    """
```

**廃止**: `gif_first_frame_as_png_base64` は `gif_frames_as_png_base64_list(gif_base64, 1)` で代替可能だが、後方互換のため残す（テストが参照しているため）。

### `_build_annotation_prompt`（変更）

```python
def _build_annotation_prompt(
    emoji_name: str,
    aliases: list[str],
    gif_frame_count: int = 0,
) -> str:
    """LLM へのアノテーション生成プロンプトを構築する（内部関数）。

    gif_frame_count > 1 の場合、プロンプト先頭にアニメーション旨を追記する。

    Args:
        emoji_name: 絵文字ファイル名（拡張子なし）。
        aliases: 絵文字の別名リスト。
        gif_frame_count: GIF から抽出したフレーム数。0 または 1 の場合は追記しない。

    Returns:
        英語の LLM プロンプト文字列。
    """
```

### `generate_annotation`（変更）

`image_base64: str` → `images: list[str]` に変更。
単一画像の場合も `images = [image_base64]` として渡すよう呼び出し側で変換。

```python
def generate_annotation(
    emoji_name: str,
    aliases: list[str],
    ollama_url: str,
    llm_model: str,
    timeout: int,
    images: list[str] | None = None,
    gif_frame_count: int = 0,
) -> str:
    """Ollama API を呼び出して絵文字のアノテーションテキストを生成する。

    images が指定された場合、Ollama のマルチモーダル機能を使って
    画像シーケンスをモデルに渡す（images フィールド）。

    Args:
        emoji_name: 絵文字ファイル名（拡張子なし）。
        aliases: 絵文字の別名リスト。
        ollama_url: Ollama サーバーのベース URL。
        llm_model: 使用する LLM モデル名。
        timeout: HTTP タイムアウト秒数。
        images: 絵文字画像の base64 文字列リスト。None または空の場合は画像なし。
        gif_frame_count: GIF から抽出したフレーム数。プロンプト修飾に使用。

    Returns:
        生成されたアノテーションテキスト。
    """
```

---

## 状態遷移（`build_all_annotations` 内の GIF 処理フロー）

```
GIF エントリ検出
  │
  ├─ gif_frames_as_png_base64_list(gif_base64, gif_max_frames)
  │    └─ [frame_1_png, frame_2_png, ..., frame_N_png]
  │
  ├─ logger.debug("Extracted %d frames from gif: %s", len(frames), name)
  │
  ├─ generate_annotation(name, aliases, ..., images=frames, gif_frame_count=len(frames))
  │    ├─ _build_annotation_prompt(name, aliases, gif_frame_count=N)
  │    │    └─ "These are N frames from an animated GIF emoji. ..."
  │    └─ Ollama /api/generate {images: [frame_1, frame_2, ..., frame_N]}
  │
  └─ record["image_base64"] = 元の GIF base64（フレームリストではない）
```
