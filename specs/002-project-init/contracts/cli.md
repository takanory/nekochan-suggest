# CLI コントラクト: nekochan-suggest

**作成日**: 2026-03-20  
**フィーチャー**: `002-project-init`  
**バージョン**: 0.1.0（スタブ）

---

## コマンド: `nekochan-suggest`

### 呼び出し形式

```
nekochan-suggest [OPTIONS] [TEXT]
nekochan-suggest build-annotations [BUILD_OPTIONS]
```

### 位置引数

| 引数 | 型 | 説明 |
|------|-----|------|
| `TEXT` | str（省略可） | 絵文字提案を求めるテキスト。省略時は標準入力から読む |

### グローバルオプション

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--count N` | int (1-10) | 3 | 返す候補数 |
| `--json` | flag | false | JSON 形式で出力 |
| `--timeout N` | int | 30 | LLM レスポンスタイムアウト（秒） |
| `--help` | flag | — | ヘルプを表示 |

### サブコマンド: `build-annotations`

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--dry-run` | flag | false | ファイル保存せずサンプルを表示 |
| `--help` | flag | — | ヘルプを表示 |

---

## 標準出力フォーマット

### テキスト形式（`--json` なし）

```
1. yatta-nya  0.87
2. niko-nya   0.82
3. hare-nya   0.79
```

形式: `{N}. {ファイル名}  {スコア（小数点以下2桁）}`

### JSON 形式（`--json` あり）

```json
{
  "suggestions": [
    {"name": "yatta-nya", "score": 0.87},
    {"name": "niko-nya",  "score": 0.82},
    {"name": "hare-nya",  "score": 0.79}
  ]
}
```

---

## 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | エラー（入力不正・LLM 接続失敗・アノテーション未生成等） |

---

## エラー出力（stderr）

エラーメッセージはすべて `stderr` に出力する。`stdout` には出力しない。

| エラー種別 | メッセージ例 |
|-----------|------------|
| 空入力 | `エラー: テキストが空です。テキストを指定してください。` |
| アノテーション未生成 | `エラー: アノテーションファイルが見つかりません。まず 'nekochan-suggest build-annotations' を実行してください。` |
| LLM 接続失敗 | `エラー: Ollama サーバーに接続できません。Ollama が起動しているか確認してください。` |
| タイムアウト | `エラー: LLM レスポンスがタイムアウトしました (30秒)。` |

---

## スタブ実装の出力（002-project-init 完了時点）

```
$ nekochan-suggest "テスト"
未実装 (別フィーチャー 001-nekochan-suggest で実装予定)

$ nekochan-suggest build-annotations
未実装 (別フィーチャー 001-nekochan-suggest で実装予定)
```

---

## コマンド: `nekochan-suggest-ui`

### 呼び出し形式

```
nekochan-suggest-ui [--help]
```

Streamlit アプリを起動し、デフォルトブラウザで開く。

### スタブ実装の出力（002-project-init 完了時点）

```
$ nekochan-suggest-ui
未実装 (別フィーチャー 001-nekochan-suggest で実装予定)
```
