# コマンドインターフェース契約: nekochan-suggest-ui

**Branch**: `004-streamlit-ui` | **Date**: 2026-05-04

---

## CLI コマンド: `nekochan-suggest-ui`

### 概要

Streamlit ベースの GUI を起動するコマンド。

### シグネチャ

```
nekochan-suggest-ui [OPTIONS]
```

### オプション

本フィーチャーのスコープでは追加 CLI オプションなし。
内部的に `streamlit run` に相当する処理を実行する。

### 正常終了の振る舞い

1. ブラウザが自動的に開き、Streamlit アプリが表示される（デフォルトポート 8501）。
2. ターミナルに Streamlit のサーバーログが出力される。
3. `Ctrl+C` で停止する。

### エラー終了の振る舞い

| 状況 | 振る舞い |
|------|---------|
| `streamlit` が未インストール | `ImportError` / `ModuleNotFoundError` が発生し、stderr にメッセージ出力 |
| ポート 8501 がビジー | Streamlit が別ポートを自動選択（Streamlit のデフォルト挙動） |

---

## ライブラリ関数契約: `suggest()`（既実装・参照のみ）

`nekochan_suggest.query.suggest` — `_app.py` が依存する唯一のビジネスロジック関数。

```python
def suggest(text: str, count: int = 3) -> list[SuggestionResult]:
    """テキストに最も類似したネコチャン絵文字を返す。

    Args:
        text: 類似絵文字を検索するテキスト。
        count: 返す候補の最大件数（デフォルト 3）。

    Returns:
        スコア降順の SuggestionResult リスト。

    Raises:
        FileNotFoundError: アノテーションファイルが存在しない場合。
        Exception: Ollama 接続失敗・埋め込みモデル未ダウンロードなど。
    """
```

### `_app.py` での呼び出し規約

- `ANNOTATIONS_PATH.exists()` を事前チェックし、非存在時は `suggest()` を呼ばない。
- `suggest()` の呼び出しは `try/except Exception` でラップし、
  例外時は `st.error()` でユーザーフレンドリーなメッセージを表示する。
- `count` は仕様上 3 固定（スライダー等によるユーザー変更はスコープ外）。

---

## 画像 URL 契約

```
https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/images/{name}.png
```

| パラメータ | 説明 |
|-----------|------|
| `{name}` | `SuggestionResult.name`（例: `"yatta-nya"`） |
| 拡張子 | `.png` 固定（GIF は `001-nekochan-suggest` でスキップ済み） |

**注意**: この URL はインターネット接続が必要。`st.image(url)` で直接表示し、
失敗時は Streamlit のデフォルト処理（壊れた画像アイコン表示）に委ねる。
候補名とスコアの表示は継続する。

---

## エントリーポイント登録（pyproject.toml）

```toml
[project.scripts]
nekochan-suggest-ui = "nekochan_suggest.ui:main"

[project.optional-dependencies]
gui = ["streamlit"]
```

**使用方法**:
```bash
uv sync --extra gui
nekochan-suggest-ui
```
