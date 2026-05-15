# Tasks: English README and CLI Localization

**Input**: Design documents from `/specs/006-english-readme-cli/`
**Prerequisites**: [plan.md](plan.md) ✅ | [spec.md](spec.md) ✅ | [research.md](research.md) ✅ | [data-model.md](data-model.md) ✅ | [contracts/cli.md](contracts/cli.md) ✅

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 並列実行可能（異なるファイル、未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー（[US1], [US2]）
- 各タスクに正確なファイルパスを記載

---

## Phase 1: セットアップ

**目的**: 変更前のベースライン確認

- [X] T001 実装開始前に `uv run pytest tests/` を実行してすべてのテストがパスすることを確認する

---

## Phase 2: User Story 1 - English README with Japanese link (Priority: P1) 🎯 MVP

**ゴール**: `README.md` を完全な英語に書き直し、日本語版 `README.ja.md` を新規作成する

**独立テスト基準**: `README.md` を開いてすべての文章・見出し・コード例が英語であること。先頭 10 行以内に `README.ja.md` へのリンクが存在すること。`README.ja.md` が存在し日本語コンテンツを含むこと

### User Story 1 の実装

- [X] T002 [US1] `README.md` を全面英語に書き直す（概要・インストール・CLI使い方・開発・ライセンスの 5 セクション）。タイトル直下 10 行以内に `README.ja.md` へのリンクを追加する in README.md
- [X] T003 [P] [US1] `README.ja.md` を新規作成する（現行実装状態を反映した日本語版: 概要・インストール・CLI使い方・開発・ライセンスの 5 セクション）in README.ja.md

**チェックポイント**: この時点で US1 は独立してテスト可能。`README.md` に日本語文字なし、`README.ja.md` 存在確認（SC-001, SC-002, SC-004）

---

## Phase 3: User Story 2 - English CLI help and output (Priority: P2)

**ゴール**: `cli.py` の argparse 文字列 7 箇所を英語化し、`pyproject.toml` の description フィールドを英語化する

**独立テスト基準**: `uv run nekochan-suggest --help` および `uv run nekochan-suggest build-annotations --help` の出力に日本語文字が含まれないこと（SC-003）

### User Story 2 の実装

- [X] T004 [US2] `_build_query_parser()` の `description`・`text` 引数 help・`--count` help・`--json` help を英語に更新する in nekochan_suggest/cli.py
- [X] T005 [US2] `_build_build_annotations_parser()` の `description`・`--dry-run` help・`--timeout` help を英語に更新する in nekochan_suggest/cli.py
- [X] T006 [P] [US2] `[project].description` フィールドを `"CLI tool to suggest nekochan emoji filenames for a given text."` に更新する in pyproject.toml

**チェックポイント**: この時点で US2 は独立してテスト可能。`--help` 出力に日本語文字なし（SC-003）

---

## Final Phase: 検証 & ポリッシュ

**目的**: 全 SC の達成確認とテスト通過

- [X] T007 `uv run pytest tests/` を実行してすべてのテストがパスすることを確認する（SC-005）
- [X] T008 [P] SC 最終確認: `grep` で `README.md` に日本語文字なし（SC-001）、`head -10 README.md` で `README.ja.md` リンク存在（SC-004）、`uv run nekochan-suggest --help` 出力に日本語なし（SC-003）

---

## 依存関係グラフ

```
T001 (ベースライン確認)
  ↓
T002 [US1]  ←── T003 [US1] (並列可)
  ↓
T004 [US2]
  ↓
T005 [US2]  ←── T006 [US2] (pyproject.toml、並列可)
  ↓
T007 (pytest)  ←── T008 (SC確認、並列可)
```

US1 と US2 は互いに独立しており、並列実装が可能。

---

## 並列実行例

### US1 並列実行

```bash
# 並列で実行可能:
# ターミナル 1: README.md 書き換え (T002)
# ターミナル 2: README.ja.md 新規作成 (T003)
```

### US2 並列実行

```bash
# T004, T005 は同一ファイル (cli.py) のため順次実行
# T006 は別ファイル (pyproject.toml) のため T004/T005 と並列可
# ターミナル 1: T004 → T005 (cli.py)
# ターミナル 2: T006 (pyproject.toml)
```

---

## 実装戦略

**MVP スコープ**: US1 のみ（T001〜T003）で PR 可能。英語 README を先行リリースし、
CLI 英語化（US2）は後続 PR として分割することも可能。

**推奨実装順序**:
1. T001 — ベースライン確認
2. T002 + T003 （並列）— US1 完了 → SC-001, SC-002, SC-004 を目視確認
3. T004 → T005 + T006（並列）— US2 完了 → SC-003 を `--help` で目視確認
4. T007 + T008（並列）— 全 SC 確認

**テスト方針**: 新規テストは追加しない（spec Assumptions）。
`tests/test_cli.py` に日本語アサーション文字列が存在しないため変更不要（research.md 調査済み）。
T007 は argparse 変更後も既存テストが壊れないことの確認。

---

## タスクカウント

| フェーズ | タスク数 | ユーザーストーリー |
|---------|---------|----------------|
| Phase 1 (Setup) | 1 | — |
| Phase 2 (US1) | 2 | US1 |
| Phase 3 (US2) | 3 | US2 |
| Final Phase | 2 | — |
| **合計** | **8** | — |

| ユーザーストーリー | タスク数 |
|----------------|---------|
| US1 (P1) | 2 |
| US2 (P2) | 3 |
