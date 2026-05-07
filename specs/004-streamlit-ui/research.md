# Research: nekochan-suggest Streamlit GUI

**Branch**: `004-streamlit-ui` | **Date**: 2026-05-04

---

## 1. `streamlit.web.cli.main_run()` の起動 API

### 決定事項
`streamlit.web.cli.main_run` は `click.core.Command`（名前: `"run"`）であり、
`target`（スクリプトパス）と `args`（追加引数）の 2 つの Argument を受け取る。
Python コードから呼び出すには以下のパターンを使用する：

```python
from streamlit.web.cli import main_run
main_run.main([str(app_path)], standalone_mode=False)
```

`standalone_mode=False` を指定することで、`SystemExit` を発生させずに戻り値を返す。

### 根拠
- streamlit 1.57.0 で動作確認済み。
- `standalone_mode=True`（デフォルト）だと click が `SystemExit(0)` を発生させるため、
  `nekochan_suggest/ui.py` の `main()` から呼び出す際は `False` を指定する。

### 代替案の検討
- `subprocess.run(["streamlit", "run", ...])`: 動作するが、パスの解決や
  venv 内の `streamlit` 実行ファイル特定が必要になる。内部 API より複雑。
- `sys.argv` 書き換え + `cli.main()`: 副作用が大きくテストが困難。

---

## 2. ファイル構成：エントリーポイントとアプリ本体の分離

### 決定事項
`nekochan_suggest/ui.py` と `nekochan_suggest/_app.py` の 2 ファイルに分離する。

```
nekochan_suggest/
├── ui.py    — console_scripts エントリーポイント（main_run を呼び出すのみ）
└── _app.py  — Streamlit アプリ本体（st.* API を使用する UI ロジック）
```

### 根拠
- `ui.py:main()` は `nekochan-suggest-ui` コンソールスクリプトとして呼び出される。
  この時点では Streamlit サーバーコンテキスト外なので `import streamlit as st` を
  トップレベルに置くのは不適切（`gui` extra 未インストール時に ImportError が発生）。
- Streamlit が `_app.py` を実行するときは、ファイルのトップレベルコードが
  毎回実行されるため、アプリ本体を独立ファイルに置くことで関心を分離できる。
- テスト時には `_app.py` の内部関数をモックするため、
  ファイル分離によってインポートが明確になる。

### 代替案の検討
- `ui.py` 単一ファイル（`if __name__ == "__main__"` ガード）:
  Streamlit の実行コンテキスト検出が複雑になる。`import streamlit` が
  コンソールスクリプト起動時にも走るため、`gui` extra 未インストール時に失敗する。

---

## 3. テスト戦略（`suggest()` モックテスト）

### 決定事項
UI レンダリング（`st.*` の呼び出し）はテスト対象としない。
代わりに以下をテストする：

1. **`_app.py` のロジック関数**: `suggest()` を `unittest.mock.patch` でモックし、
   アノテーションファイルの存在チェック・入力バリデーション・画像 URL 構築を
   純粋な Python 関数として単体テストする。
2. **`ui.py:main()`**: `main_run` をモックして、正しい引数で呼び出されることを確認。

テストファイル: `tests/test_ui.py`

### 根拠
- `streamlit.testing.v1.AppTest` は UI レンダリングのテストに使えるが、
  今回のユーザー判断（Q2 回答 B）により不採用。
- `suggest()` はすでにテスト済み（`tests/test_annotations.py` / `test_cli.py`）。
  GUI 層でビジネスロジックを再テストする必要はない。
- モックテストにより CI で Ollama・埋め込みモデルが不要となる（憲法 II 準拠）。

---

## 4. `streamlit` オプション依存の管理

### 決定事項
`pyproject.toml` の `[project.optional-dependencies]` に `gui = ["streamlit"]` を
追加する（すでに定義済み）。インストールコマンド：

```bash
uv sync --extra gui        # 開発環境
pip install nekochan-suggest[gui]  # 本番インストール
```

### 根拠
- CLI のみ使うユーザーに streamlit（41 packages、~50MB 以上）を強制しない。
- `pyproject.toml` にすでに `gui = ["streamlit"]` が定義済みのため変更不要。

### 代替案の検討
- `[project.dependencies]` への追加: 重量級依存を全ユーザーに強制するため不採用。

---

## 5. 画像 URL パターンの確認

### 決定事項
```
https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/images/<name>.png
```
このパターンは `001-nekochan-suggest` の spec.md（FR-013）および
`004-streamlit-ui` の spec.md（FR-004）で定義済み。`.png` 固定（GIF は除外済み）。

### 根拠
- `st.image(url)` に URL を直接渡す方式を採用。画像の事前キャッシュは行わない。
- インターネット未接続時は Streamlit 側でエラーになるが、候補名・スコアは表示継続（FR-004）。

---

## 6. `suggest()` 関数インターフェース（既実装）

```python
from nekochan_suggest.query import suggest, SuggestionResult, ANNOTATIONS_PATH

def suggest(text: str, count: int = 3) -> list[SuggestionResult]:
    ...

@dataclass
class SuggestionResult:
    name: str   # 絵文字ファイル名（例: "yatta-nya"）
    score: float  # コサイン類似度（0.0〜1.0）
```

`ANNOTATIONS_PATH = Path.home() / ".local" / "share" / "nekochan-suggest" / "annotations.json"`

`suggest()` は `ANNOTATIONS_PATH` が存在しない場合は `FileNotFoundError` を発生させる。
（`_app.py` で事前チェックするか、`except` でキャッチして `st.error()` で表示する。）
