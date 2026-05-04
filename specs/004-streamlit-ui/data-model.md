# データモデル: nekochan-suggest Streamlit GUI

**Branch**: `004-streamlit-ui` | **Date**: 2026-05-04

---

## エンティティ一覧

### 1. `SuggestionResult`（既実装 — `nekochan_suggest/query.py`）

| フィールド | 型 | 説明 | バリデーション |
|-----------|-----|------|--------------|
| `name` | `str` | 絵文字ファイル名（拡張子なし） | 非空文字列（例: `"yatta-nya"`） |
| `score` | `float` | コサイン類似度スコア | `0.0 ≤ score ≤ 1.0` |

**用途**: `suggest()` の戻り値。GUI はこのオブジェクトを受け取り、
`name` から画像 URL を構築し、`score` を小数点以下 3 桁で表示する。

---

### 2. `UserInput`（UI 層の概念エンティティ — コードには存在しない）

| フィールド | 型 | 説明 | バリデーション |
|-----------|-----|------|--------------|
| `text` | `str` | ユーザーが入力した文章 | 1〜1000 文字 |

**バリデーションルール**:
- 空文字列または空白のみの場合 → 入力促しメッセージを表示し、提案を実行しない
- 1000 文字超 → 先頭 1000 文字を使用し、文字数超過を通知する

---

### 3. `ImageUrl`（UI 層の導出値 — 独立クラスなし）

| 属性 | 型 | 値 |
|-----|-----|-----|
| パターン | `str` | `https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/images/{name}.png` |
| 導出元 | `SuggestionResult.name` | `name` を URL に埋め込む |

**注意**: `.png` 固定。GIF 絵文字は `001-nekochan-suggest` でスキップ済みのため
アノテーションファイルには含まれない。

---

### 4. `AnnotationsFile`（既実装 — `nekochan_suggest/query.py` の `ANNOTATIONS_PATH`）

| 属性 | 値 |
|-----|-----|
| パス | `~/.local/share/nekochan-suggest/annotations.json` |
| 形式 | JSON 配列（`[{"name": str, "annotation": str, "embedding": [float, ...]}]`） |
| 存在しない場合 | `_app.py` が起動時に `st.error()` + セットアップ案内を表示 |
| 空の場合（0 件）| `suggest()` が空リストを返す → 「候補が見つかりませんでした」を表示 |

---

## 状態遷移図

```
[起動]
  |
  v
[アノテーションファイル存在チェック]
  |                    |
  | 存在する           | 存在しない
  v                    v
[入力待ち状態]      [エラー表示状態]
  |                    |
  | テキスト入力        | 「提案する」押下（無視）
  | + 「提案する」      |
  v                    v
[提案実行中]        [エラー表示継続]
  |         \
  | 成功     \ suggest() 例外
  v           v
[結果表示]  [st.error() 表示]
  |
  | 再入力
  v
[入力待ち状態]（結果クリアなし、上書き）
```

---

## インターフェース依存関係

```
nekochan_suggest/_app.py
  └─ imports → nekochan_suggest.query.suggest()
  └─ imports → nekochan_suggest.query.ANNOTATIONS_PATH
  └─ imports → nekochan_suggest.query.SuggestionResult
  └─ imports → streamlit as st

nekochan_suggest/ui.py
  └─ imports → streamlit.web.cli.main_run  (起動時のみ)
  └─ references → nekochan_suggest/_app.py  (パスで参照)
```

---

## 新規ファイル

| ファイル | 責務 |
|---------|------|
| `nekochan_suggest/_app.py` | Streamlit アプリ本体。`st.*` API 使用。GUI ロジック全般 |
| `nekochan_suggest/ui.py` | `main()` エントリーポイント。`main_run` 呼び出しのみ（既存ファイルを更新） |
| `tests/test_ui.py` | `_app.py` のロジック関数と `ui.py:main()` のユニットテスト |
