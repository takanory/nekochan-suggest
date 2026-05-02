# 実装計画書: ネコチャン絵文字アノテーション構築コマンド（build-annotations）

**Branch**: `001-nekochan-suggest` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)

## Summary

`nekochan-suggest build-annotations` コマンドを実装する。
aliases.json を `urllib` でネットワーク取得し、Ollama API（`urllib` 直接 HTTP 呼び出し）で
各絵文字のアノテーションテキストを英語で生成し、`sentence-transformers` で埋め込みベクトルを生成して
`~/.local/share/nekochan-suggest/annotations.json` に保存する。
TDD（RED→GREEN）で実装する。

**スコープ**: US2（build-annotations コマンド）のみ。US3（Streamlit GUI）は別フィーチャー。

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**:
- `sentence-transformers`（埋め込み生成、`003-emoji-query` と共有）
- Python 標準ライブラリ: `urllib`（Ollama API HTTP 呼び出し・aliases.json 取得）、`json`、`tomllib`

**Storage**:
- 読み取り: `https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/aliases.json`
- 書き込み: `~/.local/share/nekochan-suggest/annotations.json`
- 設定: `~/.config/nekochan-suggest/config.toml`（読み取り専用）

**LLM**: Ollama API (`POST {ollama_url}/api/generate`)、デフォルト `http://localhost:11434`、`stream: false`  
**LLM Model**: `qwen3.5`（デフォルト）、`NEKOCHAN_LLM_MODEL` または `config.toml` の `llm_model` キーで変更可  
**Embed Model**: `intfloat/multilingual-e5-base`（デフォルト）、`NEKOCHAN_EMBED_MODEL` または `embed_model` キーで変更可  
**Embed Prefix**: アノテーション生成側は `"passage: "`（クエリ側は `"query: "`）  
**Timeout**: デフォルト 30 秒、`--timeout N` / `NEKOCHAN_TIMEOUT` で上書き可  
**Testing**: `pytest`, `unittest.mock`（CI 上でモデルダウンロード・Ollama サーバー不要）  

## Constitution Check

- [x] **I. Python ファースト・シンプリシティ** — 新規サードパーティ依存なし（`sentence-transformers` は既存依存）。LLM 呼び出しは `urllib` 標準ライブラリで直接 HTTP。
- [x] **II. テストファースト** — TDD サイクル。`urllib.request.urlopen` と `SentenceTransformer` を `unittest.mock` でモックし、CI でネットワーク・モデルダウンロード不要。
- [x] **III. CLI ファースト・インターフェース** — `nekochan-suggest build-annotations` が CLI エントリーポイント。`--dry-run` / `--timeout` フラグ対応。
- [x] **IV. 可観測性と型安全性** — 全公開関数に型ヒント付与。`pyrefly` 厳格モードでチェック。ライブラリコード内 `print()` 禁止。進行表示は `sys.stderr.write()` + `sys.stderr.flush()` を使用。dry-run の stdout 出力（`print(json.dumps(...))` ）は CLI の構造化出力であり、憲法 IV の禁止範囲外。
- [x] **V. 日本語ドキュメント** — 仕様書・コードコメント・docstring は日本語。エラーメッセージは英語（仕様書仕様）。

## Project Structure

### 変更・新規作成ファイル

```text
nekochan_suggest/
├── annotations.py     # 完全実装（スタブ → 実装）
├── cli.py             # _handle_build_annotations 実装・--timeout 追加
└── query.py           # _load_config() 拡張（ollama_url・timeout キー追加）

tests/
├── test_annotations.py   # 新規作成
├── test_cli.py           # _handle_build_annotations テスト追記
└── fixtures/
    └── aliases_fixture.json  # 新規作成（5件サンプル）

specs/001-nekochan-suggest/
├── plan.md    # このファイル
└── spec.md    # 既存
```

## 設計詳細

### annotations.py の関数設計

| 関数 | シグネチャ | 説明 |
|------|-----------|------|
| `fetch_aliases` | `(url: str, timeout: int) -> dict[str, list[str]]` | aliases.json を `urllib` でネットワーク取得 |
| `_build_annotation_prompt` | `(emoji_name: str, aliases: list[str]) -> str` | LLM へのプロンプトを構築（内部関数） |
| `generate_annotation` | `(emoji_name: str, aliases: list[str], ollama_url: str, llm_model: str, timeout: int) -> str` | Ollama API でアノテーション生成 |
| `generate_embedding` | `(text: str, embed_model: str) -> list[float]` | `sentence-transformers` で埋め込みベクトル生成（`"passage: "` プレフィックス） |
| `load_existing_annotations` | `(path: Path) -> list[dict[str, object]]` | 既存 JSON を読み込む（不在→空リスト） |
| `save_annotations_file` | `(records: list[dict[str, object]], path: Path) -> None` | JSON を上書き保存（親ディレクトリ自動作成） |
| `build_all_annotations` | `(dry_run: bool, config: dict[str, str]) -> None` | メインオーケストレーション |

### annotations.json レコード構造

```json
[
  {
    "name": "yatta-nya",
    "annotation": "A cat celebrating with joy. Use when expressing success, achievement, or excitement.",
    "embedding": [0.0231, -0.1456, ...]
  }
]
```

（003-emoji-query の `_load_annotations()` が期待する構造と完全互換）

### build_all_annotations アルゴリズム

```
1. try:
     aliases_dict = fetch_aliases(ALIASES_URL, timeout)
   except OSError as e:
     raise ValueError(f"failed to fetch aliases.json from {ALIASES_URL}: {e}") from e
   # → aliases_dict: dict[str, list[str]]
2. load_existing_annotations(ANNOTATIONS_PATH) → existing_records
3. existing_names = {r["name"] for r in existing_records}
4. records = list(existing_records)  # 既存レコードをコピー
5. skipped = []
6. for i, (name, alias_list) in enumerate(aliases_dict.items()):
     if name in existing_names: continue  # 再開ロジック
     進行表示: sys.stderr.write(f"[{i+1}/{total}] {name}\r"); sys.stderr.flush()
     try:
       annotation = generate_annotation(name, alias_list, ...)
       embedding = generate_embedding(annotation, embed_model)
       record = {"name": name, "annotation": annotation, "embedding": embedding}
       if dry_run:
         if i < 3: print(json.dumps(record, ensure_ascii=False))  # stdout への構造化出力（CLI 出力）
         continue
       records.append(record)
       save_annotations_file(records, path)  # 1件ごと全上書き
     except Exception as e:
       skipped.append(name)
       logging.warning(...)
7. if skipped: sys.stderr.write(f"Skipped: {skipped}\n"); sys.stderr.flush()
```

### 設定キー一覧（_load_config() 拡張後）

| キー | 環境変数 | 設定ファイルキー | デフォルト |
|------|---------|----------------|----------|
| `embed_model` | `NEKOCHAN_EMBED_MODEL` | `embed_model` | `"intfloat/multilingual-e5-base"` |
| `llm_model` | `NEKOCHAN_LLM_MODEL` | `llm_model` | `"qwen3.5"` |
| `ollama_url` | `NEKOCHAN_OLLAMA_URL` | `ollama_url` | `"http://localhost:11434"` |
| `timeout` | `NEKOCHAN_TIMEOUT` | `timeout` | `"30"` |

### Ollama API 呼び出し

```python
# POST {ollama_url}/api/generate
payload = {
    "model": llm_model,
    "prompt": prompt,
    "stream": False,
}
# レスポンス JSON: {"response": "...", ...}
```

### エラーメッセージ一覧

| 状況 | stderr メッセージ | 終了コード |
|------|----------------|----------|
| aliases.json フェッチ失敗（network） | `Error: failed to fetch aliases.json from {url}: {message}` | 1 |
| aliases.json フェッチ失敗（HTTP 非200） | `Error: failed to fetch aliases.json: HTTP {status}` | 1 |
| Ollama 未起動 / 接続失敗 | `Error: failed to connect to Ollama at {url}. Is Ollama running?` | 1 |
| 1件処理エラー（スキップ） | 完了後に `Skipped N emojis: name1, name2, ...` | 0（処理続行） |

## 検証計画

1. `uv run pytest tests/test_annotations.py tests/test_cli.py -v -m "not integration"` — 全 PASS
2. `uv run pytest --cov=nekochan_suggest --cov-report=term-missing -m "not integration"` — `annotations.py` ≥80%
3. `uv run pyrefly check nekochan_suggest/` — エラー 0
4. 手動: `ollama` 稼働環境で `nekochan-suggest build-annotations --dry-run` — 3 件プレビュー・exit 0
