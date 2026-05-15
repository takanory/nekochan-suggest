# Research: GIF Multi-Frame Annotation Generation

**Feature**: `005-gif-multi-frame`  
**Date**: 2026-05-08  
**Status**: Complete — NEEDS CLARIFICATION なし

---

## 1. Pillow による GIF フレーム反復処理

**Decision**: `img.seek(n)` + `.convert("RGBA")` パターンを使用する。

**Rationale**:
- `img.seek(n)` はフレーム境界を超えると `EOFError` を送出する標準的な API。
- GIF のパレットモード（P モード）は `seek` 後に変化することがあるため、毎フレーム明示的に `.convert("RGBA")` してから PNG 変換する。
- 既存の `gif_first_frame_as_png_base64` が同パターンを使用しており一貫性がある。

**Alternatives considered**:
- `ImageSequence.Iterator`: 高レベル API だが、特定インデックスへのランダムアクセスが困難。均等間隔サンプリングのためには `seek(idx)` が適切。
- `GifImagePlugin.LOADING_STRATEGY`: プロセス全体に影響するグローバル設定のため採用しない。

**実装メモ**:
```python
n_frames = getattr(img, "n_frames", 1)
frame_indices = (
    [i * (n_frames - 1) // (max_frames - 1) for i in range(max_frames)]
    if max_frames > 1
    else [0]
)
for idx in frame_indices:
    img.seek(idx)
    frame = img.convert("RGBA")
    ...
```

---

## 2. Ollama マルチイメージリクエスト

**Decision**: `/api/generate` の `images` フィールドに base64 リストを渡す（既存方式の拡張）。

**Rationale**:
- Ollama 公式 API ドキュメントに `images` は "a list of base64-encoded images" と明記されており、複数画像が公式サポートされている。
- 単一リクエストで複数フレームを渡すことで LLM がシーケンスを一度に評価できる。
- 現在の `generate_annotation` は `body["images"] = [image_base64]` で単一要素リストを渡している。複数フレームの場合は `body["images"] = frames_list` に変更するだけで対応可能。

**Alternatives considered**:
- フレームごとに個別リクエスト + 結果マージ: 実装が複雑、API 呼び出しが N 倍になりコスト増。

---

## 3. `NEKOCHAN_GIF_MAX_FRAMES` 環境変数バリデーション

**Decision**: `_load_config()` 内でパース・バリデーションし、0 以下・非整数の場合はデフォルト 4 を WARNING ログとともに使用する。

**Rationale**:
- CLI ツールとして不正な環境変数でクラッシュさせるより、デフォルトへの graceful fallback が適切（spec の Edge Cases に明記）。
- WARNING ログにより、ユーザーが設定ミスを気づける。

**実装メモ**: `_load_config` に `gif_max_frames` キーを追加し、`str` として返す（他の設定値と統一）。`build_all_annotations` で `int(config["gif_max_frames"])` に変換。

---

## 4. Pillow の `pyproject.toml` への追加

**Decision**: `[project.dependencies]` (core) に `"pillow>=10.0"` を追加する。

**Rationale**:
- GIF 処理は `build-annotations` の中核機能であり optional ではない。
- Pillow はすでに `.venv` にインストール済みで事実上の必須依存。
- `>=10.0`（2023年5月リリース）は GIF API が安定しており、RGBA 変換の挙動が確定している。

**Alternatives considered**:
- `[project.optional-dependencies]` への追加: 手動インストールが必要になり使い勝手が悪い。

---

## 解決済みの NEEDS CLARIFICATION

| 項目 | 解決内容 |
|------|---------|
| サンプリングアルゴリズム | `i * (total-1) // (N-1)`、N=1 は index 0 のみ（spec.md で確定済み） |
| プロンプト修正 | "These are N frames from an animated GIF emoji." を先頭に追記（spec.md で確定済み） |
| 既存エントリ再生成 | マルチフレーム方式で上書き再生成（spec.md で確定済み） |
| Pillow 追加先 | core dependencies（本ドキュメントで確定） |
| ログ出力 | DEBUG レベルで抽出フレーム数を出力（spec.md で確定済み） |
