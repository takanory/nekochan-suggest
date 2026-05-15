# Implementation Plan: English README and CLI Localization

**Branch**: `006-english-readme-cli` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/006-english-readme-cli/spec.md`

## Summary

`README.md` を英語に書き直し、日本語版を `README.ja.md` として分離する。
`nekochan_suggest/cli.py` の `argparse` ヘルプ文字列を英語に更新し、
`pyproject.toml` の `description` フィールドも英語化する。
既存テストのアサーション文字列を更新する。新規コードの追加はなく、
既存文字列の置き換えのみ。新規依存関係なし。

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: `argparse`（標準ライブラリ）— 新規依存なし  
**Storage**: N/A（コード・ドキュメントの文字列変更のみ）  
**Testing**: pytest（既存テストのアサーション文字列を更新）  
**Target Platform**: macOS / Linux（CLI ツール）  
**Project Type**: CLI ツール  
**Performance Goals**: N/A  
**Constraints**: テスト追加なし; Streamlit UI および Python logging メッセージは対象外  
**Scale/Scope**: 変更対象: `README.md`（書き換え）, `README.ja.md`（新規）, `nekochan_suggest/cli.py`（argparse 文字列 7 箇所）, `pyproject.toml`（description フィールド）, `tests/test_cli.py`（アサーション文字列）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Python ファースト・シンプリシティ** — Python 3.13+ のみ。新規サードパーティ依存なし。
  文字列の変更のみであり、新モジュールを追加しない。YAGNI 適用済み。
- [x] **II. テストファースト** — 既存テストの文字列アサーションを更新するのみ。
  新規ロジックなし、LLM 呼び出しなし。SC-005 は `uv run pytest` でパスを確認。
- [x] **III. CLI ファースト・インターフェース** — 本フィーチャーは CLI の
  argparse ヘルプ文字列を英語化するもの。CLI エントリーポイントに変更なし。
- [x] **IV. 可観測性と型安全性** — 新規関数・型ヒントの追加なし。
  既存コードの型安全性を変更しない。
- [x] **V. 日本語ドキュメント** — **意図的な違反・正当化あり（下記）**:
  `README.md` を英語にすること自体がこのフィーチャーの目的である。
  `README.ja.md` により日本語ドキュメントは維持される。
  `cli.py` の argparse 文字列は英語化するが、コードコメント・docstring は
  日本語のままとする（対象外）。

> **V 違反の正当化**: 国際的な OSS 配布（GitHub / PyPI）において英語の
> `README.md` は標準要件。日本語ユーザーは `README.ja.md` でカバーされる。
> CLI ヘルプ文字列の英語化はユーザー向けインターフェースの一部であり、
> 内部ドキュメント（docstring/コメント）とは区別される。

## Project Structure

### Documentation (this feature)

```text
specs/006-english-readme-cli/
├── plan.md              # このファイル
├── research.md          # Phase 0 調査結果
├── data-model.md        # Phase 1 データモデル
├── quickstart.md        # Phase 1 クイックスタート
├── contracts/
│   └── cli.md           # CLI コントラクト（英語ヘルプ文字列）
└── tasks.md             # Phase 2 タスク一覧（/speckit.tasks で生成）
```

### Source Code (repository root)

```text
README.md                         ← 全面英語に書き換え（リンク追加）
README.ja.md                      ← 新規作成（最新実装を反映した日本語版）
pyproject.toml                    ← description フィールドのみ更新
nekochan_suggest/
└── cli.py                        ← argparse 文字列 7 箇所を英語化
tests/
└── test_cli.py                   ← 日本語アサーション文字列を英語に更新
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。新規ファイルは
`README.ja.md` のみ。変更はすべて既存ファイルへの文字列置き換え。

## Complexity Tracking

> **V. 日本語ドキュメント 違反の正当化**

| 違反 | 理由 | より単純な代替案を却下した理由 |
|------|------|-------------------------------|
| `README.md` を英語で記述 | フィーチャーの目的そのもの | 英語化なしでは FR-001〜004 を満たせない |
| CLI argparse 文字列を英語化 | 国際 CI パイプライン対応、`--help` の英語化 | 日本語のままでは FR-004 を満たせない |

---

## Constitution Check（Phase 1 事後再確認）

*Phase 1 設計完了後、全原則に追加違反がないことを確認。*

- [x] **I** — 新規依存なし。新規モジュールなし。設計変更なし。
- [x] **II** — `tests/test_cli.py` の既存アサーション調査結果、日本語アサーション文字列なし。
  `uv run pytest tests/` が argparse 変更後もパスすることをタスク完了条件とする。
- [x] **III** — CLI コントラクト（`contracts/cli.md`）が英語ヘルプ出力を定義済み。
- [x] **IV** — 型安全性に変更なし。新規 `print()` なし。
- [x] **V** — 違反は初回確認時に正当化済み。追加違反なし。
