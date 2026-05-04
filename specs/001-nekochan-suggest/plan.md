# 実装計画書: ネコチャン絵文字アノテーション構築コマンド（build-annotations）

**ブランチ**: `001-nekochan-suggest` | **日付**: 2026-05-04 | **仕様書**: [spec.md](spec.md)  
**入力**: `/specs/001-nekochan-suggest/spec.md`

## サマリー

sphinx-nekochan プロジェクトの全絵文字（378件）に対して、Ollama（`qwen3.5:2b`、マルチモーダル）を使ったアノテーションテキストの生成と、`sentence-transformers`（`intfloat/multilingual-e5-base`）による埋め込みベクトルの事前計算・永続化を行う `build-annotations` コマンドを実装する。GIF 画像はマルチモーダルモデル非対応のためスキップする。**T001〜T013 は全実装済み・テスト済み。** 本計画書は実装後の設計記録として作成する。

## 技術コンテキスト

**言語/バージョン**: Python 3.14.2（`uv` 管理、`.venv` 使用）  
**主要依存関係**:
- `sentence-transformers`（埋め込み生成、`intfloat/multilingual-e5-base`）
- `urllib`（標準ライブラリ、Ollama API HTTP 呼び出し）
- `json`, `tomllib`, `pathlib`（標準ライブラリ）
- Ollama ローカルサーバー（外部ランタイム、`qwen3.5:2b`）

**ストレージ**: `~/.local/share/nekochan-suggest/annotations.json`（JSON ファイル）  
**テスト**: `pytest` + `pytest-cov` + `unittest.mock`（モックで CI をオフライン化）  
**ターゲットプラットフォーム**: macOS / Linux デスクトップ  
**プロジェクト種別**: CLI ツール + ライブラリ  
**パフォーマンス目標**: LLM 呼び出しを除くロジック処理 1 秒以内（SC-001）  
**制約**: `ollama` PyPI パッケージ不使用・外部 HTTP ライブラリ不使用  
**スケール/スコープ**: 絵文字 378 件、GIF 以外のすべてにアノテーション生成

## 憲法チェック

*ゲート: Phase 0 リサーチ前に合格必須。Phase 1 設計後に再チェック済み。*

- [x] **I. Python ファースト・シンプリシティ** — Python 3.14.2 で実装済み。追加 PyPI 依存は `sentence-transformers` のみ（埋め込み生成に必須、正当化済み）。`annotations.py`（アノテーション生成・永続化）、`query.py`（設定・検索）、`cli.py`（エントリーポイント）が単一責務を持つ。
- [x] **II. テストファースト** — TDD（RED→GREEN）で実施済み。LLM 呼び出しは `unittest.mock` でモック済み（CI にサーバー不要）。`annotations.py` カバレッジ 100%、全体 95%。
- [x] **III. CLI ファースト・インターフェース** — `nekochan-suggest build-annotations [--dry-run] [--timeout N]` を実装済み。`build_all_annotations()` は純粋な Python 関数として直接インポート可能。`--json` は本コマンドの出力形式として N/A（アノテーション保存が目的のため）。
- [x] **IV. 可観測性と型安全性** — 全公開関数に型ヒント付与済み。`pyrefly check nekochan_suggest/` エラー 0 件。`logging` モジュールを使用し、ライブラリコード内の `print()` は dry-run プレビュー出力（CLI 構造化出力、憲法 III 範囲内）のみ。
- [x] **V. 日本語ドキュメント** — 仕様書・計画書・docstring・コードコメントはすべて日本語で記述済み。

> 違反なし。Complexity Tracking セクション省略。

## プロジェクト構造

### ドキュメント（本フィーチャー）

```text
specs/001-nekochan-suggest/
├── plan.md          # このファイル
├── research.md      # Phase 0 出力（設計上の決定記録）
├── data-model.md    # Phase 1 出力（AnnotationRecord・外部データソース）
├── quickstart.md    # Phase 1 出力（インストール・実行ガイド）
└── tasks.md         # 実装タスク（Phase 1〜5、T001〜T021 合計 21 件）
```

### ソースコード

```text
nekochan_suggest/
├── __init__.py         # パッケージ初期化
├── annotations.py      # アノテーション生成・保存（本フィーチャー主体）
├── cli.py              # CLI エントリーポイント（build-annotations サブコマンド）
├── query.py            # 設定読み込み・埋め込み検索
└── ui.py               # Streamlit GUI（別フィーチャー対象）

tests/
├── fixtures/
│   └── aliases_fixture.json
├── test_annotations.py  # annotations.py ユニット/統合テスト（28件）
├── test_cli.py          # CLI テスト
└── test_query.py        # query.py テスト
```

**構造決定**: 単一プロジェクト構成（Option 1）。CLI ツール + ライブラリ。GUI（`ui.py`）は別フィーチャー対象のため本計画書では対象外。
