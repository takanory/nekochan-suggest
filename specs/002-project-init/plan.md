# 実装計画書: プロジェクト初期化

**Branch**: `002-project-init` | **Date**: 2026-03-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-project-init/spec.md`

## サマリー

`uv` を使った Python パッケージ `nekochan_suggest` を初期化する。
`nekochan-suggest`（CLI）と `nekochan-suggest-ui`（GUI）の 2 つのエントリーポイントを持ち、
この時点ではすべてスタブ実装とする。`ruff`・`pyrefly`・`pytest` のセットアップと
`Makefile` によるタスクランナーを整備し、後続フィーチャーの開発基盤を確立する。

## Technical Context

**Language/Version**: Python 3.11+（`tomllib` 標準搭載の最低バージョン。憲法は 3.13+ を指定するが、
  後述の Complexity Tracking を参照）  
**Primary Dependencies**: なし（コアは標準ライブラリのみ）。開発依存: `pytest`, `ruff`, `pyrefly`。
  オプション依存: `streamlit`（GUI グループ）  
**Storage**: N/A（このフィーチャーはスキャフォールドのみ）  
**Testing**: `pytest`  
**Target Platform**: macOS / Linux（CLI ツール）  
**Project Type**: CLI ツール / ライブラリパッケージ  
**Performance Goals**: `nekochan-suggest --help` < 1 秒  
**Constraints**: コア機能は標準ライブラリのみで動作すること。`streamlit` はオプション依存として分離  
**Scale/Scope**: 単一開発者、小規模ツール。5 モジュールのフラット構成

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Python ファースト・シンプリシティ** — Python 3.11+（Complexity Tracking に正当化を記載）。
  コアの外部依存ゼロ。各モジュール（`cli.py`・`query.py`・`annotations.py`・`ui.py`）が
  単一の責務を持つ。開発依存（ruff・pyrefly・pytest）は計画書に明記済み。
- [x] **II. テストファースト** — pytest をセットアップし、パッケージインポートと
  CLI エントリーポイントの基本動作を検証する初期テストを実装する。
  LLM 呼び出しはこのフィーチャーのスコープ外のためモック不要。
- [x] **III. CLI ファースト・インターフェース** — `nekochan-suggest`（位置引数 + `build-annotations` サブコマンド）
  のエントリーポイントを提供。`--help` で引数・オプション一覧を表示。`--json` は後続フィーチャーで実装（スタブのみ）。
- [x] **IV. 可観測性と型安全性** — 全スタブ関数に型ヒントを付与。`pyrefly` 厳格モードで
  `nekochan_suggest/` をチェック。`ruff` リントによりライブラリコード内の裸の `print()` を検出。
- [x] **V. 日本語ドキュメント** — README・docstring・コードコメントはすべて日本語で記述する。

## Project Structure

### Documentation (this feature)

```text
specs/002-project-init/
├── plan.md              # このファイル
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
└── contracts/           # Phase 1 出力（N/A: 外部インターフェースなし）
```

### Source Code (repository root)

```text
nekochan_suggest/          # メインパッケージ（フラット構成）
├── __init__.py            # パッケージ初期化
├── cli.py                 # CLIエントリーポイント・引数解析
├── query.py               # 埋め込みベクトル検索ロジック（スタブ）
├── annotations.py         # アノテーション生成・保存ロジック（スタブ）
└── ui.py                  # Streamlit GUI（スタブ）

tests/
└── test_cli.py            # CLI エントリーポイントの基本動作テスト

Makefile                   # lint / format / typecheck / test / check ターゲット
pyproject.toml             # パッケージ定義・依存・ruff・pyrefly 設定
README.md                  # インストール手順・使い方
```

**Structure Decision**: 5 モジュールのフラット構成を採用。サブパッケージ化はプロジェクト規模から不要。
`tests/` はパッケージ外に分離し `pytest` が自動検出する。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Python 3.11+（憲法は 3.13+ を指定） | `tomllib` は 3.11 から標準ライブラリに含まれる。対象ユーザー環境に 3.11/3.12 が想定される | 3.13 に固定すると現行 macOS デフォルト環境で動作しない可能性があり、セットアップコストが上がる |
