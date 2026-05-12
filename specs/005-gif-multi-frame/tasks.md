# Tasks: GIF Multi-Frame Annotation Generation

**Input**: Design documents from `/specs/005-gif-multi-frame/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 異なるファイルを対象とし、未完了タスクへの依存がないため並列実行可能
- **[Story]**: 対象ユーザーストーリー（US1, US2）
- 各タスクには具体的なファイルパスを記載

---

## Phase 1: Setup（共有インフラ）

**Purpose**: pyproject.toml への Pillow 追加。他のすべてのフェーズの前提。

- [X] T001 `pyproject.toml` の `[project.dependencies]` に `"pillow>=10.0"` を追加し `uv sync` を実行する

**Checkpoint**: `uv run python -c "from PIL import Image; print('OK')"` が成功すること

---

## Phase 2: Foundational（ブロッキング前提）

このフィーチャーは既存モジュールの拡張のみのため、独立した Foundational フェーズは不要。  
Phase 1 完了後、Phase 3（US1）を即座に開始可能。

---

## Phase 3: User Story 1 — Animated GIF produces richer annotation (Priority: P1) 🎯 MVP

**Goal**: GIF を複数フレームに分解して Ollama に渡し、アニメーション文脈を反映したアノテーションを生成する。

**Independent Test**:
```bash
nekochan-suggest build-annotations --dry-run
# GIF 絵文字エントリに複数フレームが渡されることを pytest で確認
uv run pytest tests/test_annotations.py -v
```

### Tests for User Story 1 ⚠️ これらを先に書き、FAIL を確認してから実装する

- [X] T002 [US1] `TestGifFramesAsPngBase64List` クラスを `tests/test_annotations.py` に追加する — テストケース: 複数フレーム返却・単一フレーム GIF・フレーム数が max_frames 未満・均等間隔サンプリング検証（10フレーム/max=4 → indices 0,3,6,9）・PNG base64 出力確認・壊れた GIF バイト列（無効データ）を渡すと `Exception`（`OSError` 等）が送出されること（FR-010, EC-002）
- [X] T003 [US1] `TestBuildAnnotationPromptWithGifFrameCount` クラスを `tests/test_annotations.py` に追加する — テストケース: gif_frame_count=0 でプレフィックスなし・gif_frame_count=1 でプレフィックスなし・gif_frame_count=4 で "These are 4 frames from an animated GIF emoji." が先頭に追記される
- [X] T004 [US1] `TestGenerateAnnotation` に images リスト対応テストを追加する（`tests/test_annotations.py`） — テストケース: `images=[frame1, frame2]` が `body["images"]` として送信される・`images=None` のとき images フィールドなし・`gif_frame_count=2` が `_build_annotation_prompt` に渡される
- [X] T005 [US1] `TestBuildAllAnnotations` にマルチフレーム動作テストを追加する（`tests/test_annotations.py`） — テストケース: GIF エントリに `gif_frames_as_png_base64_list` が呼ばれる・PNG 単一画像エントリに `generate_annotation(images=[png_b64])` が呼ばれる・GIF の既存エントリが再生成される（スキップされない）・DEBUG ログ "Extracted N frames from gif: {name}" が出力される

### Implementation for User Story 1

- [X] T006 [US1] `gif_frames_as_png_base64_list(gif_base64: str, max_frames: int) -> list[str]` を `nekochan_suggest/annotations.py` に実装する — Pillow `img.seek(idx)` + `.convert("RGBA")` + PNG 変換、サンプリング式 `i * (total-1) // (N-1)`、N=1 は index 0 のみ、日本語 docstring 付き（T002 テストが PASS になること）
- [X] T007 [US1] `_build_annotation_prompt` に `gif_frame_count: int = 0` パラメータを追加し `nekochan_suggest/annotations.py` を更新する — gif_frame_count > 1 のとき `"These are {gif_frame_count} frames from an animated GIF emoji. "` をプロンプト先頭に追記（T003 テストが PASS になること）
- [X] T008 [US1] `generate_annotation` のシグネチャを `image_base64: str = ""` → `images: list[str] | None = None, gif_frame_count: int = 0` に変更し `nekochan_suggest/annotations.py` を更新する — `images` が非空のとき `body["images"] = images`、`gif_frame_count` を `_build_annotation_prompt` に渡す（T004 テストが PASS になること）
- [X] T009 [US1] `build_all_annotations` を `nekochan_suggest/annotations.py` で更新する — GIF 処理: `gif_first_frame_as_png_base64` 呼び出しを `gif_frames_as_png_base64_list(image_b64, gif_max_frames)` に置き換え、`logger.debug("Extracted %d frames from gif: %s", len(frames), name)` を追加、`generate_annotation(images=frames, gif_frame_count=len(frames))` に更新、非 GIF 画像は `generate_annotation(images=[image_b64])` として渡す、GIF 既存エントリの再生成：mimetype が `"image/gif"` の既存エントリは `existing_names` から除外してスキップしない（T005 テストが PASS になること）

**Checkpoint**: `uv run pytest tests/test_annotations.py -v` が全テスト PASS、`NEKOCHAN_GIF_MAX_FRAMES` 未設定でのデフォルト動作確認

---

## Phase 4: User Story 2 — Frame count is configurable (Priority: P2)

**Goal**: `NEKOCHAN_GIF_MAX_FRAMES` 環境変数で GIF フレーム上限を制御できる。

**Independent Test**:
```bash
NEKOCHAN_GIF_MAX_FRAMES=2 nekochan-suggest build-annotations --dry-run
```

### Tests for User Story 2 ⚠️ これらを先に書き、FAIL を確認してから実装する

- [X] T010 [US2] `TestLoadConfig` クラスまたは既存テストに `gif_max_frames` テストを追加する（`tests/test_query.py`） — テストケース: 環境変数未設定 → `"4"` を返す・`NEKOCHAN_GIF_MAX_FRAMES=2` → `"2"` を返す
- [X] T011 [US2] `TestBuildAllAnnotations` に gif_max_frames バリデーションテストを追加する（`tests/test_annotations.py`） — テストケース: `gif_max_frames="0"` → デフォルト 4 を使用（WARNING ログ）・`gif_max_frames="-1"` → デフォルト 4 を使用（WARNING ログ）・`gif_max_frames="abc"` → デフォルト 4 を使用（WARNING ログ）・`gif_max_frames="2"` → `gif_frames_as_png_base64_list` に `max_frames=2` が渡される

### Implementation for User Story 2

- [X] T012 [P] [US2] `_load_config` に `gif_max_frames` キーを追加し `nekochan_suggest/query.py` を更新する — `NEKOCHAN_GIF_MAX_FRAMES` 環境変数（デフォルト `"4"`）を読み込み、返す辞書に `"gif_max_frames": str(gif_max_frames)` を追加（T010 テストが PASS になること）
- [X] T013 [US2] `build_all_annotations` で `config["gif_max_frames"]` を取得してバリデーション後に `gif_frames_as_png_base64_list` に渡す処理を `nekochan_suggest/annotations.py` に追加する — 変換失敗・0 以下の場合 `logger.warning(...)` でデフォルト 4 を使用（T011 テストが PASS になること）

**Checkpoint**: `NEKOCHAN_GIF_MAX_FRAMES=2 uv run pytest tests/ -v` が全テスト PASS

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 型安全性・コード品質・ドキュメント確認

- [X] T014 [P] `uv run pyrefly nekochan_suggest/` を実行し、新規・変更関数の型ヒントエラーをすべて修正する
- [X] T015 [P] `uv run ruff check . && uv run ruff format --check .` を実行し、指摘をすべて修正する
- [X] T016 `uv run pytest tests/test_annotations.py --cov=nekochan_suggest/annotations --cov-report=term-missing` を実行し `gif_frames_as_png_base64_list` のカバレッジが 100% であることを確認する（SC-004）
- [X] T017 変更した関数（`gif_frames_as_png_base64_list`、`_build_annotation_prompt`、`generate_annotation`、`build_all_annotations`）の docstring とインラインコメントが日本語で記述されていることを確認し、`gif_first_frame_as_png_base64` の docstring に deprecated 旨（代わりに `gif_frames_as_png_base64_list(gif_base64, 1)` を使用すること）を日本語で追記する（原則 V）
- [ ] T018 [P] [US1] `nekochan-suggest build-annotations --dry-run` を実行し、出力された GIF 絵文字 5 件のアノテーションにアニメーション的な文脈（動き・反復動作の表現）が含まれていることを手動確認する（SC-002）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即座に開始可能
- **User Story 1 (Phase 3)**: Phase 1 完了後に開始可能
- **User Story 2 (Phase 4)**: Phase 3 の T008（`generate_annotation` 変更）完了後に開始可能（T012 は独立して進められる）
- **Polish (Phase 5)**: Phase 3 + Phase 4 完了後

### User Story Dependencies

- **US1 (P1)**: Phase 1 完了後に開始可能。他のストーリーへの依存なし。
- **US2 (P2)**: T012（`_load_config` 変更）は US1 と独立して並列実装可能。T013 は T009 に依存。

### US1 内の実行順序

```
T002→T003→T004→T005（テスト作成・順次）
T006（T002 FAIL 確認後）
T007（T003 FAIL 確認後）
T008（T004 FAIL 確認後）
T009（T005 FAIL 確認後、T006+T007+T008 完了後）
```

---

## Parallel Example: User Story 1

```bash
# T006, T007, T008 は異なる関数を対象とするが同一ファイルのため順次実行推奨
# ただし T012 (query.py) は T006-T009 と並列実行可能

# US1 実装完了後の検証:
uv run pytest tests/test_annotations.py::TestGifFramesAsPngBase64List -v
uv run pytest tests/test_annotations.py::TestBuildAnnotationPromptWithGifFrameCount -v
uv run pytest tests/test_annotations.py::TestGenerateAnnotation -v
uv run pytest tests/test_annotations.py::TestBuildAllAnnotations -v
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 完了: Pillow を core deps に追加
2. Phase 3 完了: マルチフレーム GIF 抽出・プロンプト修正・generate_annotation 更新・build_all_annotations 更新
3. **STOP & VALIDATE**: `uv run pytest tests/test_annotations.py -v` で全 PASS 確認
4. `nekochan-suggest build-annotations --dry-run` で GIF エントリの複数フレーム動作を目視確認

### Incremental Delivery

1. Setup（T001）→ Foundation 準備完了
2. US1（T002–T009）→ テスト独立検証 → MVP デモ可能
3. US2（T010–T013）→ テスト独立検証 → 環境変数制御可能
4. Polish（T014–T017）→ PR 作成・マージ
