# nekochan-suggest

> For English documentation, see [README.md](README.md).

文章に合ったネコチャン絵文字のファイル名を提案する CLI / GUI ツール。ローカル LLM によるアノテーション生成と埋め込みベクトル検索を組み合わせて動作します。

## 概要

`nekochan-suggest` はテキストを入力として受け取り、意味的に最も近い [nekochan](https://github.com/nekochanapp/nekochan) 絵文字のファイル名を類似度順に返します。アノテーションは [Ollama](https://ollama.com/) を使用してローカルで生成し、検索には [sentence-transformers](https://www.sbert.net/) による埋め込みベクトルを使用します。

## インストール

[uv](https://docs.astral.sh/uv/) が必要です。

```bash
# 開発用依存関係も含めてインストール
uv sync
```

GUI（Streamlit）を使用する場合:

```bash
uv sync --extra gui
```

## 使い方

### CLI

```bash
# テキストから絵文字を提案
nekochan-suggest "今日はとても眠い"

# 候補数を指定（デフォルト: 3）
nekochan-suggest --count 5 "今日はとても眠い"

# JSON 形式で出力
nekochan-suggest --json "今日はとても眠い"

# アノテーションをビルド（または再ビルド）
nekochan-suggest build-annotations

# ドライラン: 保存せず先頭 3 件をプレビュー表示
nekochan-suggest build-annotations --dry-run

# Ollama への HTTP タイムアウトを指定（秒）
nekochan-suggest build-annotations --timeout 60

# ヘルプを表示
nekochan-suggest --help
nekochan-suggest build-annotations --help
```

### GUI

```bash
nekochan-suggest-ui
```

### `build-annotations` の事前準備

1. [Ollama](https://ollama.com/) をインストールして起動する:
   ```bash
   ollama serve
   ollama pull gemma4:e4b
   ```
2. アノテーションをビルドする（初回は時間がかかります）:
   ```bash
   nekochan-suggest build-annotations
   ```

アノテーションは `~/.local/share/nekochan-suggest/annotations.json` に保存されます。  
特定の絵文字を再生成したい場合は、そのエントリをファイルから削除してから `build-annotations` を再実行してください。

### GIF アニメーション対応

GIF 形式の絵文字は複数フレームを抽出して LLM に渡し、アニメーションの文脈を考慮したアノテーションを生成します。

## 開発

```bash
# リンティング
make lint

# フォーマット
make format

# 型検査
make typecheck

# テスト
make test

# 全チェック（CI 相当）
make check
```

## ライセンス

[LICENSE](LICENSE) を参照してください。
