# Implementation Plan: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**Branch**: `003-emoji-query` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-emoji-query/spec.md`

## Summary

ユーザーが入力したテキストを `nomic-embed-text` モデルで埋め込みベクトルに変換し、
事前生成済みアノテーションファイル（`~/.local/share/nekochan-suggest/annotations.json`）
内の各レコードとのコサイン類似度を純 Python (`math` モジュール) で計算して上位 N 件を返す。
既存の `query.py` スタブを本実装に置き換え、`cli.py` の `_handle_query` を完成させる。
ollama 通信には `ollama` PyPI パッケージ、設定読み込みには標準ライブラリ `tomllib` を使用する。

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml 現行制約。憲法は 3.13+ を推奨するが
`tomllib` (3.11+) で十分なため現制約を維持する）  
**Primary Dependencies**: `ollama` PyPI パッケージ（埋め込み生成のみ。コサイン類似度は stdlib `math` で実装）  
**Storage**: `~/.local/share/nekochan-suggest/annotations.json`（読み取り専用）、
`~/.config/nekochan-suggest/config.toml`（読み取り専用）  
**Testing**: `pytest`, `pytest-cov`, `unittest.mock`（CI 上で Ollama 不要）  
**Target Platform**: macOS / Linux CLI  
**Project Type**: CLI ツール + ライブラリ API  
**Performance Goals**: 埋め込み生成を除く処理（入力解析・類似度計算・出力整形）が 1 秒以内（SC-001）  
**Constraints**: 追加 PyPI 依存は `ollama` のみ。コサイン類似度は numpy 禁止・純 Python 実装  
**Scale/Scope**: アノテーション ~378 件、単一ユーザー CLI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*根拠: 憲法バージョン 2.0.1（原則 I〜V）*

- [x] **I. Python ファースト・シンプリシティ** — Python 3.11+（憲法推奨 3.13+ に近い）。
  新規サードパーティ依存は `ollama` のみ（埋め込み生成という具体的要件で正当化）。
  `query.py` はクエリロジック単一責務、`cli.py` は引数解析・出力整形単一責務。
- [x] **II. テストファースト** — テストを先に記述する（TDD サイクル）。
  `ollama` 呼び出しは `unittest.mock` でモックし CI で Ollama 不要。
  `query.py` の純 Python ロジックは決定論的テストが可能。行カバレッジ ≥ 80% 達成可能。
- [x] **III. CLI ファースト・インターフェース** — `nekochan-suggest "text"` が CLI エントリーポイント。
  ライブラリ API `suggest(text, count, timeout)` が CLI を反映。`--json` フラグ実装済み。
- [x] **IV. 可観測性と型安全性** — 全公開関数に型ヒント付与。`pyrefly` 厳格モードでチェック。
  `logging` モジュールで構造化ログ（ライブラリ内 `print()` 禁止）。
- [x] **V. 日本語ドキュメント** — 仕様書・計画書・コードコメント・docstring はすべて日本語。

> **判定（Phase 0 前）**: 全ゲート通過。Complexity Tracking への記載不要。

### Post-Design Re-Check（Phase 1 設計完了後）

- [x] **I. Python ファースト・シンプリシティ** — `query.py`（クエリロジック）・`cli.py`（入出力）の
  単一責務分担を data-model.md・contracts/cli.md で確認済み。
  新規依存 `ollama` は埋め込み生成という具体的要件により正当化。
- [x] **II. テストファースト** — `tests/fixtures/annotations.json` ダミーデータと
  `unittest.mock.patch('ollama.Client')` でモックテスト設計済み（data-model.md 参照）。
  CI で Ollama 不要。コサイン類似度等の純 Python ロジックは決定論的テスト可能。
- [x] **III. CLI ファースト・インターフェース** — contracts/cli.md に CLI コントラクト定義済み。
  `suggest(text, count, timeout)` ライブラリ API が CLI を反映。`--json` フラグ対応。
- [x] **IV. 可観測性と型安全性** — `SuggestionResult` dataclass と `suggest()` に型ヒント付与予定。
  `logging` モジュール使用（ライブラリ内 `print()` 禁止、CLI 出力は `print()` で可）。
- [x] **V. 日本語ドキュメント** — data-model.md・research.md・contracts/cli.md・quickstart.md
  はすべて日本語。エラーメッセージは英語（仕様書仕様）で、これはドキュメント規則の例外。

> **Post-Design 判定**: 全ゲート通過。実装フェーズへ進んで問題なし。

## Project Structure

### ドキュメント（本フィーチャー）

```text
specs/003-emoji-query/
├── plan.md              # このファイル（/speckit.plan 出力）
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
├── contracts/           # Phase 1 出力
│   └── cli.md
└── tasks.md             # Phase 2 出力（/speckit.tasks コマンド）
```

### ソースコード（リポジトリルート）

```text
nekochan_suggest/
├── __init__.py          # バージョン定義（既存・変更なし）
├── annotations.py       # build-annotations ロジック（既存・変更なし）
├── cli.py               # CLIエントリーポイント（既存・_handle_query を完成）
├── query.py             # クエリビジネスロジック（既存スタブ → 本実装）
└── ui.py                # Streamlit UI（既存・変更なし）

tests/
├── fixtures/
│   └── annotations.json # テスト用ダミーデータ（新規）
├── test_cli.py          # CLI統合テスト（既存・追記）
└── test_query.py        # query.py 単体テスト（新規）
```

**Structure Decision**: 既存の単一パッケージ構成 (`nekochan_suggest/`) を維持。
`src/` レイアウトへの移行は行わない（スコープ外）。

## Complexity Tracking

> 全ゲート通過のため記載なし。
