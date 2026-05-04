# クイックスタート: nekochan-suggest Streamlit GUI

**Branch**: `004-streamlit-ui` | **Date**: 2026-05-04

---

## 前提条件

- `001-nekochan-suggest` の実装が完了していること（`annotations.json` が構築済み）
- Python 3.13+ と `uv` がインストールされていること
- Ollama が起動済みで `qwen3.5:2b` モデルが利用可能なこと（アノテーション構築時のみ）

---

## セットアップ

### 1. GUI オプション依存をインストール

```bash
cd nekochan-suggest
uv sync --extra gui
```

### 2. アノテーションファイルを構築（未実施の場合）

```bash
nekochan-suggest build-annotations
```

実行後、`~/.local/share/nekochan-suggest/annotations.json` が生成される。

---

## GUI の起動

```bash
nekochan-suggest-ui
```

コマンド実行後、ブラウザが自動的に開き、Streamlit アプリが表示される（デフォルト: `http://localhost:8501`）。

---

## 使い方

1. テキスト入力欄に文章を入力する（例: 「今日も頑張ろう！」）
2. 「提案する」ボタンをクリックする
3. 候補が 3 件表示される：
   - 絵文字名（例: `yatta-nya`）
   - コサイン類似度スコア（例: `0.856`）
   - ネコチャン画像（GitHub Raw URL から取得）

### アノテーションファイルが存在しない場合

GUI 起動時にエラーメッセージが表示される：

```
アノテーションファイルが見つかりません。
以下のコマンドを実行してアノテーションを構築してください：
  nekochan-suggest build-annotations
```

---

## 停止方法

ターミナルで `Ctrl+C` を押す。

---

## トラブルシューティング

### `ModuleNotFoundError: No module named 'streamlit'`

GUI オプション依存がインストールされていない。以下を実行：

```bash
uv sync --extra gui
```

### 提案ボタンを押してもエラーが表示される

- Ollama が起動しているか確認: `ollama ps`
- 埋め込みモデルがダウンロード済みか確認:
  ```python
  from sentence_transformers import SentenceTransformer
  SentenceTransformer("intfloat/multilingual-e5-base")
  ```

### 画像が表示されない

インターネット接続を確認してください。
画像は `https://raw.githubusercontent.com/takanory/sphinx-nekochan/...` から取得されます。
画像が取得できない場合でも、絵文字名とスコアは表示されます。
