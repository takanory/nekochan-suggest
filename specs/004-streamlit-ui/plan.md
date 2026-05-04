# Implementation Plan: nekochan-suggest Streamlit GUI

**Branch**: `004-streamlit-ui` | **Date**: 2026-05-04 | **Spec**: [specs/004-streamlit-ui/spec.md](spec.md)
**Input**: Feature specification from `/specs/004-streamlit-ui/spec.md`

## Summary

`nekochan-suggest-ui` コマンドで Streamlit ベースの GUI を起動し、
テキスト入力から `suggest()` を呼び出してネコチャン絵文字の候補（名前・スコア・画像）を
縦方向カードレイアウトで表示する。
エントリーポイント（`ui.py`）とアプリ本体（`_app.py`）を分離し、
`streamlit.web.cli.main_run` で起動する。

## Technical Context

**Language/Version**: Python 3.13+（`uv` 管理、`.venv` 使用）
**Primary Dependencies**: `streamlit>=1.57.0`（optional `[gui]` extra）、既存: `sentence-transformers`
**Storage**: `~/.local/share/nekochan-suggest/annotations.json`（読み取りのみ）
**Testing**: `pytest` + `unittest.mock`（`streamlit.testing.v1.AppTest` は不使用）
**Target Platform**: macOS / Linux ローカル実行
**Project Type**: CLI + GUI ツール
**Performance Goals**: GUI 起動 10 秒以内（SC-001）、提案表示 5 秒以内（SC-002）
**Constraints**: ローカル起動のみ、`streamlit` はオプション依存、インターネット接続で画像表示
**Scale/Scope**: シングルユーザー、ローカル専用

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Python-First Simplicity** — Python 3.13+ のみ。`streamlit` は `[gui]` optional extra として
  正当化済み（重量級 GUI ライブラリを CLI ユーザーに強制しない）。
  `_app.py` は UI 表示のみ、`ui.py` は起動のみと責務が明確に分離されている。
- [x] **II. テストファースト** — TDD を適用する。`suggest()` は `unittest.mock.patch` でモック化し
  CI でモデル起動不要。UI レンダリング（st.* 描画）はテスト対象外（Q2 回答 B）。
  ビジネスロジック関数（アノテーション存在チェック・URL 構築・入力バリデーション）は
  単体テストで ≥ 80% カバレッジを維持する。
- [x] **III. CLI-First Interface** — `nekochan-suggest-ui` コンソールスクリプトが定義済み。
  GUI はビジネスロジックを持たず、`suggest()` ライブラリ関数を呼び出す薄い表示層のみ。
  **例外**: GUI フィーチャーとして `--json` フラグ・stdin/stdout プロトコルは非適用。
  Streamlit はブラウザ UI を提供するため、CLI プロトコルとは独立する（正当化済み）。
- [x] **IV. 可観測性と型安全性** — 全公開関数に型ヒント付与。`pyrefly` 厳格モードでチェック。
  ライブラリコードに `print()` 不使用。エラーは `st.error()` で可視化、スタックトレース非表示。
- [x] **V. 日本語ドキュメント** — 仕様書・計画書・コードコメント・docstring はすべて日本語で記述。

## Project Structure

### Documentation (this feature)

```text
specs/004-streamlit-ui/
├── plan.md              # このファイル（/speckit.plan 出力）
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
├── contracts/
│   └── cli-contract.md  # Phase 1 出力
└── tasks.md             # Phase 2 出力（/speckit.tasks コマンドで生成）
```

### Source Code (repository root)

```text
nekochan_suggest/
├── ui.py        # 既存（更新）: main() エントリーポイント、main_run 呼び出しのみ
└── _app.py      # 新規: Streamlit アプリ本体（UI ロジック、st.* API 使用）

tests/
└── test_ui.py   # 新規: ui.py と _app.py のユニットテスト
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。
`nekochan_suggest/` に `_app.py` を追加し、`ui.py` を更新するのみ。

## Complexity Tracking

> Constitution Check は全原則クリアのため、複雑性の正当化は不要。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 原則 III: `--json` / stdin/stdout 非対応 | Streamlit は独自のブラウザ UI プロトコルを持つため CLI プロトコルと競合する | Streamlit を使わない CLI 版 suggest は 001 フィーチャーで既実装済み |

---

## Phase 0: Research 完了

**Output**: [research.md](research.md)

| 調査項目 | 結論 |
|---------|------|
| `main_run` API | `click.core.Command`、`main_run.main([str(app_path)], standalone_mode=False)` で呼び出し |
| ファイル分割 | `ui.py`（エントリーポイント）＋ `_app.py`（アプリ本体）の 2 ファイル構成 |
| テスト戦略 | `suggest()` を `unittest.mock.patch` でモック、UI レンダリングはテストしない |
| 依存管理 | `pyproject.toml` の `gui = ["streamlit"]` がすでに定義済み |
| 画像 URL | `.png` 固定、`st.image(url)` で直接表示 |
| `suggest()` I/F | 既実装 `query.py:suggest(text, count=3) -> list[SuggestionResult]` |

---

## Phase 1: Design

### data-model.md → [data-model.md](data-model.md)

| エンティティ | 説明 | 状態 |
|-------------|------|------|
| `SuggestionResult` | `name`（str）+ `score`（float）| 既実装 |
| `UserInput` | テキスト入力（1〜1000 文字）| UI 概念のみ |
| `ImageUrl` | `https://.../{name}.png` 導出値 | UI 計算ロジック |
| `AnnotationsFile` | `~/.local/share/.../annotations.json` | 既実装 |

### contracts/ → [contracts/cli-contract.md](contracts/cli-contract.md)

- `nekochan-suggest-ui` CLI コマンド契約
- `suggest()` 呼び出し規約（事前チェック・例外ハンドリング）
- 画像 URL パターン契約

### quickstart.md → [quickstart.md](quickstart.md)

- インストール（`uv sync --extra gui`）
- GUI 起動（`nekochan-suggest-ui`）
- 使い方・トラブルシューティング

---

## Post-Design Constitution Check

- [x] **I**: `_app.py` の責務は UI 表示のみ。`suggest()` を呼び出すだけでビジネスロジックなし。
- [x] **II**: `test_ui.py` でアノテーション存在チェック・URL 構築・バリデーションをモックテスト。
- [x] **III**: `nekochan-suggest-ui` コンソールスクリプトが `ui.py:main()` を呼び出す構造。
- [x] **IV**: `_app.py` と `ui.py` の全公開関数に型ヒント。`pyrefly` チェック対象。
- [x] **V**: `_app.py` の docstring・コメントは日本語で記述。
