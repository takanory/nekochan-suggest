# クイックスタート: プロジェクト初期化

**作成日**: 2026-03-20  
**フィーチャー**: `002-project-init`

---

## 前提条件

- Python 3.11 以上（`python --version` で確認）
- `uv` のインストール（`curl -LsSf https://astral.sh/uv/install.sh | sh`）

---

## セットアップ手順

```bash
# 1. リポジトリをクローン
git clone <repo-url> nekochan-suggest
cd nekochan-suggest

# 2. 依存関係をインストール（uv が仮想環境を自動作成）
uv sync

# 3. 動作確認
uv run nekochan-suggest --help
```

### GUI（streamlit）を使う場合

```bash
uv sync --extra gui
uv run nekochan-suggest-ui --help
```

---

## 開発タスク

```bash
# リントチェック
make lint

# コードフォーマット（自動修正）
make format

# 型チェック
make typecheck

# テスト実行
make test

# すべてまとめて実行（lint → typecheck → test）
make check
```

---

## プロジェクト構造

```
nekochan_suggest/        # メインパッケージ
├── __init__.py
├── cli.py               # CLI エントリーポイント
├── query.py             # クエリロジック（スタブ）
├── annotations.py       # アノテーション生成（スタブ）
└── ui.py                # Streamlit GUI（スタブ）

tests/
└── test_cli.py          # 基本動作テスト

Makefile                 # 開発タスクランナー
pyproject.toml           # プロジェクト設定
README.md                # 利用者向けドキュメント
```

---

## 現時点の動作（スタブ実装）

```bash
$ uv run nekochan-suggest "今日はいい天気"
未実装 (別フィーチャー 001-nekochan-suggest で実装予定)

$ uv run nekochan-suggest build-annotations
未実装 (別フィーチャー 001-nekochan-suggest で実装予定)

$ uv run nekochan-suggest --help
usage: nekochan-suggest [-h] [--count N] [--json] [--timeout N]
                        [{TEXT} | build-annotations]
...
```

---

## 次のステップ

このフィーチャー完了後、`001-nekochan-suggest` ブランチで以下を実装する:
1. `build-annotations` — アノテーション生成・埋め込みベクトル保存
2. `nekochan-suggest "文章"` — 類似度検索による絵文字提案
3. `nekochan-suggest-ui` — Streamlit GUI の実装
