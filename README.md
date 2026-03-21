# nekochan-suggest

文章に合ったネコチャン絵文字のファイル名を提案する CLI / GUI ツール。

> **Note**: コアロジック（埋め込み検索・LLM アノテーション）は別フィーチャー
> `001-nekochan-suggest` で実装予定。現バージョンはプロジェクト初期化スタブです。

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
# テキストから絵文字を提案（スタブ: 未実装メッセージを表示）
nekochan-suggest "今日はとても眠い"

# 候補数を指定
nekochan-suggest --count 5 "今日はとても眠い"

# JSON 形式で出力（スタブ）
nekochan-suggest --json "今日はとても眠い"

# アノテーションをビルド（スタブ）
nekochan-suggest build-annotations

# ヘルプ
nekochan-suggest --help
```

### GUI

```bash
nekochan-suggest-ui
```

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
