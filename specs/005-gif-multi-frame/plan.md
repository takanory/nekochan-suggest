# Implementation Plan: GIF Multi-Frame Annotation Generation

**Branch**: `005-gif-multi-frame` | **Date**: 2026-05-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-gif-multi-frame/spec.md`

## Summary

`build-annotations` コマンドにおいて、アニメーション GIF 絵文字を Pillow で複数フレームに分解し、
均等間隔サンプリング（`i * (total-1) // (N-1)`）した最大 N フレームを PNG 変換して
Ollama `images` 配列に渡すことでより豊かなアノテーションを生成する。
フレーム上限は `NEKOCHAN_GIF_MAX_FRAMES` 環境変数で制御可能（デフォルト 4）。

## Technical Context

**Language/Version**: Python 3.14.2（`uv` 管理、`.venv`）  
**Primary Dependencies**: Pillow（GIF フレーム抽出）、Ollama HTTP API（LLM）、sentence-transformers（埋め込み）  
**Storage**: `~/.local/share/nekochan-suggest/annotations.json`（JSON ファイル）  
**Testing**: pytest + pytest-cov、unittest.mock  
**Target Platform**: macOS / Linux（ローカル実行）  
**Project Type**: CLI ツール + ライブラリ  
**Performance Goals**: GIF 1 件あたり同等 PNG の 3 倍以内の処理時間（SC-003）  
**Constraints**: Ollama はオフライン必須、Pillow は core deps に追加、フレームは永続化しない  
**Scale/Scope**: ねこちゃん絵文字セット（数百件規模）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Python-First Simplicity** — Python 3.14.2。新規依存は Pillow のみ（GIF フレーム抽出に標準ライブラリでは不可能）。`gif_frames_as_png_base64_list` は単一責務。グローバル可変状態なし。
- [x] **II. テストファースト** — フレーム抽出関数・サンプリングロジック・プロンプト修正はすべて TDD で実装。LLM 呼び出しは `unittest.mock` でモック。SC-004 で 100% カバレッジ必須。
- [x] **III. CLI-First Interface** — 既存の `build-annotations` CLI に環境変数追加のみ。新規 CLI コマンドなし。
- [x] **IV. 可観測性と型安全性** — 公開関数に型ヒント付与、`pyrefly` チェック対象。NF-001 に従い DEBUG ログ追加。`print()` は使用しない。
- [x] **V. 日本語ドキュメント** — docstring・コメント・計画書は日本語で記述する。

**ゲート結果**: PASS — 違反なし。

## Project Structure

### Documentation (this feature)

```text
specs/005-gif-multi-frame/
├── plan.md              # このファイル (/speckit.plan コマンド出力)
├── research.md          # Phase 0 出力 (/speckit.plan コマンド)
├── data-model.md        # Phase 1 出力 (/speckit.plan コマンド)
├── quickstart.md        # Phase 1 出力 (/speckit.plan コマンド)
└── tasks.md             # Phase 2 出力 (/speckit.tasks コマンド — /speckit.plan では生成しない)
```

### Source Code (repository root)

```text
nekochan_suggest/
├── annotations.py       # 変更: gif_first_frame_as_png_base64 → gif_frames_as_png_base64_list
│                        #       _build_annotation_prompt に gif_frame_count パラメータ追加
│                        #       build_all_annotations に NEKOCHAN_GIF_MAX_FRAMES 対応
└── query.py             # 変更: _load_config に gif_max_frames を追加

tests/
├── test_annotations.py  # 変更: 新規フレーム抽出・サンプリング・プロンプト修正テスト追加
└── test_query.py        # 変更: _load_config に gif_max_frames テスト追加
```

**Structure Decision**: 単一プロジェクト（Option 1）。変更対象は既存モジュール `annotations.py` と `query.py` のみ。新規ファイルなし。
