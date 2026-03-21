# データモデル: プロジェクト初期化

**作成日**: 2026-03-20  
**フィーチャー**: `002-project-init`

## 概要

このフィーチャーはプロジェクトのスキャフォールドのみを行う。
新規のビジネスデータエンティティは存在しない。
定義するのはパッケージ構造とモジュール間の依存関係のみ。

---

## パッケージ構造

### `nekochan_suggest` パッケージ（フラット構成）

| モジュール | 責務 | 外部依存 | 状態 |
|-----------|------|---------|------|
| `__init__.py` | パッケージバージョン定義 | なし | スタブ |
| `cli.py` | CLIエントリーポイント・引数解析・サブコマンドディスパッチ | なし | スタブ |
| `query.py` | 埋め込みベクトル検索・コサイン類似度計算 | なし（urllib のみ） | スタブ |
| `annotations.py` | アノテーション生成・埋め込み生成・JSONファイル読み書き | なし（urllib, json のみ） | スタブ |
| `ui.py` | Streamlit GUI の起動・画面レンダリング | `streamlit`（オプション） | スタブ |

### モジュール依存関係

```
cli.py
├── query.py        （クエリ実行時）
└── annotations.py  （build-annotations 時）

ui.py
└── query.py        （提案取得時）

annotations.py
└── （標準ライブラリのみ: urllib, json, tomllib）

query.py
└── （標準ライブラリのみ: urllib, json, math）
```

---

## 設定ファイル構造

このフィーチャーで作成するが、実際の読み込みロジックは後続フィーチャーで実装。

### `~/.config/nekochan-suggest/config.toml`（将来のユーザー設定）
```toml
# フィールドは後続フィーチャー（001-nekochan-suggest）で定義される
# ここでは存在のみを定義する
```

### `pyproject.toml`（プロジェクト設定）

| セクション | 内容 |
|-----------|------|
| `[project]` | 名前・バージョン・Python 要件・エントリーポイント |
| `[project.optional-dependencies]` | `gui = ["streamlit"]` |
| `[dependency-groups]` | `dev = ["pytest", "ruff", "pyrefly"]` |
| `[tool.ruff]` | リント設定（ルール・対象・バージョン） |
| `[tool.ruff.lint]` | `select = ["E","F","I","N","UP"]` |
| `[tool.pyrefly]` | 型チェック対象ディレクトリ |
| `[tool.pytest.ini_options]` | テスト設定 |

---

## 状態遷移

このフィーチャーのスタブ実装では状態遷移は存在しない。
各コマンドはプレースホルダーメッセージを出力して終了する。
