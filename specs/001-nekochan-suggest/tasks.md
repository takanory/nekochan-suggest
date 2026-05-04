# タスクリスト: ネコチャン絵文字アノテーション構築コマンド（build-annotations）

**入力**: `/specs/001-nekochan-suggest/` 配下の設計ドキュメント  
**前提条件**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅  
**TDD**: 憲法原則 II に従い、すべての実装タスクの前にテストを先に記述する（RED → GREEN）  
**スコープ**: US2（build-annotations コマンド）のみ。US3（GUI）は別フィーチャー  
**更新日**: 2026-05-04（マルチモーダル拡張フェーズを追加）

## 表記: `[ID] [P?] [US?] 説明`

- **[P]**: 並列実行可能（別ファイル・完了待ち依存なし）
- **[US2]**: ユーザーストーリー 2（build-annotations）

---

## Phase 1: セットアップ（設定拡張・フィクスチャ準備）

**目的**: `_load_config()` への `ollama_url`・`timeout` 追加とテスト用フィクスチャの準備

- [X] T001 `nekochan_suggest/query.py` の `_load_config()` を拡張する。既存の `embed_model`・`llm_model` に加えて `ollama_url`（環境変数 `NEKOCHAN_OLLAMA_URL` / 設定キー `ollama_url` / デフォルト `"http://localhost:11434"`）と `timeout`（環境変数 `NEKOCHAN_TIMEOUT` / 設定キー `timeout` / デフォルト `"30"`）を返り値 `dict[str, str]` に追加する。既存テスト（`test_query.py`）が PASS し続けることを確認する（`nekochan_suggest/query.py`）
- [X] T002 [P] `tests/fixtures/aliases_fixture.json` を作成する。aliases.json と同じ `{"emoji-name": ["alias1", ...]}` 形式で正常レコード 4 件（例: `yatta-nya`, `nemui-nya`, `niko-nya`, `hare-nya`）とエイリアスが空リストのレコード 1 件（例: `haniwa-nya-spin`）を含める（`tests/fixtures/aliases_fixture.json`）

*T001・T002 は独立して並列実行可*

**チェックポイント**: `uv run pytest tests/ -m "not integration" -q` が全 PASS

---

## Phase 2: ユーザーストーリー 2 — アノテーションデータベースを構築・更新する（優先度: P2）

**目標**: `nekochan-suggest build-annotations` を実行すると全絵文字のアノテーションファイルが生成・保存される

**独立テスト**:
```bash
nekochan-suggest build-annotations --dry-run
# → 先頭 3 件のアノテーション JSON が stdout に表示（Ollama 稼働・ネットワーク接続が必要）
```

### ユーザーストーリー 2 のテスト（TDD — RED フェーズ）

> **⚠️ 注意: T003〜T007 はすべて FAIL することを確認してから T008 以降の実装に進むこと**

- [X] T003 [P] [US2] `tests/test_annotations.py` に `fetch_aliases()` の単体テストを `unittest.mock.patch('urllib.request.urlopen')` でモックして記述する。正常系: dict を返すこと（`{"yatta-nya": ["yatta"]}` 形式）、接続エラー（`OSError`）は伝播すること、HTTP 非200 ステータス（例: 404）は `ValueError` を送出すること（`tests/test_annotations.py`）
- [X] T004 [P] [US2] `tests/test_annotations.py` に `generate_annotation()` の単体テストを `unittest.mock.patch('urllib.request.urlopen')` でモックして記述する。正常系: `str` を返すこと（Ollama `response` フィールドを抽出）、タイムアウト（`TimeoutError`）は伝播すること、接続失敗（`ConnectionRefusedError` / `OSError`）は伝播すること（`tests/test_annotations.py`）
- [X] T005 [P] [US2] `tests/test_annotations.py` に `generate_embedding()` の単体テストを `unittest.mock.patch('sentence_transformers.SentenceTransformer')` でモックして記述する。正常系: `list[float]` を返すこと、`encode()` の引数に `"passage: "` プレフィックスが付与されること（`tests/test_annotations.py`）
- [X] T006 [P] [US2] `tests/test_annotations.py` に `build_all_annotations()` の結合テストをモック関数（`fetch_aliases`・`generate_annotation`・`generate_embedding`・`load_existing_annotations`・`save_annotations_file`）でモックして記述する。パッチ先: `nekochan_suggest.annotations.fetch_aliases`・`nekochan_suggest.annotations.generate_annotation`・`nekochan_suggest.annotations.generate_embedding`・`nekochan_suggest.annotations.load_existing_annotations`（戻り値: `[]`）・`nekochan_suggest.annotations.save_annotations_file`。ドライラン: stdout に先頭 3 件の JSON プレビューが出力されること・`save_annotations_file` が呼ばれないこと、通常実行: `save_annotations_file` が各レコード処理後に呼ばれること、再実行（再開）: `load_existing_annotations` の戻り値に既存名が含まれる場合にそのレコードをスキップすること（`load_existing_annotations` を `[{"name": "yatta-nya", ...}]` を返すように設定）、1件 LLM エラー: スキップして残りを処理し完了後にスキップ一覧を stderr に出力すること、aliases フェッチ `OSError`: `ValueError` として伝播すること（`fetch_aliases` が `OSError` を送出するようモックし `build_all_annotations` が `ValueError` を raise することを確認）、進行表示: `[N/total] 絵文字名` 形式が stderr に出力されること（`tests/test_annotations.py`）
- [X] T007 [P] [US2] `tests/test_cli.py` に `_handle_build_annotations()` のテストを `unittest.mock.patch('nekochan_suggest.cli.build_all_annotations')` でモックして追記する。`--dry-run` フラグで `build_all_annotations(dry_run=True, config=...)` が呼ばれること、`--timeout 60` で `config["timeout"]` が `"60"` に上書きされること、aliases fetch 失敗（`ValueError`）で stderr に `Error: failed to fetch aliases.json:` を含むメッセージが出力され終了コード 1 になること、Ollama 未起動（`OSError`）で stderr に `Error: failed to connect to Ollama` を含むメッセージが出力され終了コード 1 になること（`tests/test_cli.py`）

### ユーザーストーリー 2 の実装

- [X] T008 [US2] `nekochan_suggest/annotations.py` を完全実装する（既存スタブをすべて書き直す）。以下の関数を実装する:
  - `ALIASES_URL = "https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/aliases.json"`（定数）
  - `fetch_aliases(url: str, timeout: int) -> dict[str, list[str]]`: `urllib.request.urlopen` で GET 取得・HTTP 非200 は `ValueError` を送出・JSON をデコードして返す
  - `_build_annotation_prompt(emoji_name: str, aliases: list[str]) -> str`: 英語 2〜3 文のアノテーション生成プロンプトを構築する（内部関数）
  - `generate_annotation(emoji_name: str, aliases: list[str], ollama_url: str, llm_model: str, timeout: int) -> str`: `POST {ollama_url}/api/generate`（`stream: false`）を `urllib` で呼び出し・レスポンスの `"response"` フィールドを返す
  - `generate_embedding(text: str, embed_model: str) -> list[float]`: `sentence_transformers.SentenceTransformer(embed_model).encode("passage: " + text).tolist()` で埋め込みを生成する
  - `load_existing_annotations(path: Path) -> list[dict[str, object]]`: 既存 JSON を読み込む（ファイル不在は空リスト）
  - `save_annotations_file(records: list[dict[str, object]], path: Path) -> None`: 親ディレクトリを自動作成して JSON を上書き保存する
  - `build_all_annotations(dry_run: bool, config: dict[str, str]) -> None`: 全絵文字の処理を統括する。`from .query import ANNOTATIONS_PATH` を使用。ライブラリコード内 `print()` 禁止。進行表示は `sys.stderr.write(f"[{i}/{total}] {name}\r"); sys.stderr.flush()` を使用。dry-run の stdout 出力（`print(json.dumps(...))`）は CLI 構造化出力のため憲法 IV 禁止範囲外。**F1 対応**: `fetch_aliases()` 呼び出しを `try/except OSError` でラップし `ValueError(f"failed to fetch aliases.json from {url}: {e}")` に変換する（これにより `_handle_build_annotations` で `ValueError` → aliases 失敗、`OSError` → Ollama 失敗 と正しく区別できる）（`nekochan_suggest/annotations.py`）

- [X] T009 [US2] `nekochan_suggest/cli.py` の `_handle_build_annotations` を完全実装し `_build_build_annotations_parser()` に `--timeout` オプションを追加する。①`_build_build_annotations_parser()` に `--timeout`（`-t`）オプション（`int`、省略可）を追加する ②`_handle_build_annotations(args)` を実装: `_load_config()` で設定取得 → `args.timeout` が指定されていれば `config["timeout"]` を上書き → `build_all_annotations(dry_run=args.dry_run, config=config)` を `try/except` で呼び出し → `ValueError`（aliases 取得失敗）は `"Error: failed to fetch aliases.json: {message}"` を stderr に出力して終了コード 1 → `OSError` は `"Error: failed to connect to Ollama at {url}. Is Ollama running?"` を stderr に出力して終了コード 1（`nekochan_suggest/cli.py`）

**チェックポイント**: `nekochan-suggest build-annotations --dry-run` が実行できる（アノテーション生成を除く引数解析・設定読み込みが正常動作）。T003–T009 の全テストがパス

---

---

## 実装ストラテジー

**MVP スコープ**: T001〜T009 が完了すると `build-annotations` コマンドが動作可能。
T010〜T013 は品質保証フェーズ。

**TDD サイクル**:
1. Phase 1 でインフラ準備
2. T003〜T007 を並列で記述（全 FAIL を確認）
3. T008 → T009 の順で GREEN にする
4. Phase 4 でマルチモーダル拡張
5. Phase 5 で品質を高める

**SC-001（手動確認済み）**: `nekochan-suggest build-annotations --dry-run` + クエリの LLM 除外処理時間を計測。モックテスト実行（134 秒）から LLM / 埋め込み時間を除いたロジック処理は 1 秒以内であることを 2026-05-04 に確認済み。

**技術制約（実装時の注意事項）**:
1. **LLM 呼び出し**: `urllib.request.urlopen` で `POST {ollama_url}/api/generate`。`"stream": False`
2. **埋め込みプレフィックス**: `build-annotations` 側は `"passage: "`（query 側は `"query: "` と区別）
3. **1件ごと全 JSON 上書き**: `save_annotations_file` を処理ループ内で毎回呼ぶ
4. **再開ロジック**: ループ前に `load_existing_annotations()` で既存名セットを作成しスキップ
5. **ドライラン**: ファイル書き込みなし・最初の 3 件を stdout に JSON 形式でプリント
6. **進行表示**: `print(f"[{i}/{total}] {name}", end="\r", file=sys.stderr, flush=True)`
7. **`ANNOTATIONS_PATH` の再利用**: `from .query import ANNOTATIONS_PATH` を使う（再定義しない）
8. **ライブラリコード内 `print()` 禁止**: `logging` を使用。進行表示は `sys.stderr.write()` + `sys.stderr.flush()`。dry-run の stdout 出力（`print(json.dumps(...))`）は CLI 構造化出力のため憲法 IV 禁止範囲外

---

## Phase 4: US2 マルチモーダル拡張（nekochan_emoji.json・GIF スキップ）

**目的**: `nekochan_emoji.json` から画像データを取得し、Ollama のマルチモーダル機能で PNG 画像を LLM に渡す。GIF 画像はスキップして stderr に報告する。

**独立テスト**:
```bash
uv run pytest tests/test_annotations.py -v -k "emoji or gif or image"
# → 関連テストが全 PASS
```

- [X] T014 [P] [US2] `nekochan_suggest/annotations.py` に `fetch_emoji_data()` 関数を追加する。`NEKOCHAN_EMOJI_URL` 定数と `fetch_emoji_data(url: str, timeout: int) -> dict[str, dict[str, object]]` を実装する（`fetch_aliases()` と同じ urllib パターン）。テストを `tests/test_annotations.py` の `TestFetchEmojiData` クラスに追加する（正常系・OSError 伝播・HTTP 非 200 ValueError）（`nekochan_suggest/annotations.py`, `tests/test_annotations.py`）
- [X] T015 [P] [US2] `nekochan_suggest/annotations.py` の `generate_annotation()` に `image_base64: str = ""` 引数を追加し、非空の場合 Ollama リクエストに `"images": [image_base64]` フィールドを追加する。テストを `tests/test_annotations.py` に追加する（`test_sends_images_when_image_base64_given`・`test_no_images_field_when_image_base64_empty`）（`nekochan_suggest/annotations.py`, `tests/test_annotations.py`）
- [X] T016 [US2] `nekochan_suggest/annotations.py` の `build_all_annotations()` を拡張する。①`fetch_emoji_data()` 呼び出し（OSError → ValueError にラップ）を追加 ②ループ内で `emoji_data` から `mimetype` と `base64` を取得 ③`mimetype == "image/gif"` の場合 `continue` でスキップ（`skipped_gif` リストに追加）④PNG の場合は `image_b64` を `generate_annotation()` に渡す ⑤`record` に `image_base64` と `image_mimetype` フィールドを追加する。テストを `tests/test_annotations.py` に追加する（`test_gif_image_not_passed_to_llm`・`test_missing_emoji_data_uses_empty_strings`・`test_fetch_emoji_oserror_raised_as_value_error`）（`nekochan_suggest/annotations.py`, `tests/test_annotations.py`）
- [X] T017 [P] [US2] `nekochan_suggest/annotations.py` の `build_all_annotations()` 完了後に GIF スキップ一覧を stderr に出力する（LLM エラースキップとは別メッセージで分けて報告）。テストを `tests/test_annotations.py` に追加する（`test_gif_skipped_reported_to_stderr`）（`nekochan_suggest/annotations.py`, `tests/test_annotations.py`）
- [X] T018 [P] `nekochan_suggest/annotations.py` の `NEKOCHAN_EMOJI_URL` を `refs/heads/main` から `main` に正規化する（`ALIASES_URL` と統一）（`nekochan_suggest/annotations.py`）

**チェックポイント**: `uv run pytest tests/test_annotations.py -v` が 28 件全 PASS ✅

---

## Phase 5: 仕上げ・横断的関心事

**目的**: 型チェック・docstring・カバレッジ・手動検証・設計ドキュメント整備

- [X] T010 [P] `nekochan_suggest/annotations.py`・`nekochan_suggest/cli.py`・`nekochan_suggest/query.py` のすべての公開・非公開シンボルに完全な型アノテーションを付与する。`uv run pyrefly check nekochan_suggest/` を実行して報告されたエラーをすべて修正する（`nekochan_suggest/annotations.py`、`nekochan_suggest/cli.py`、`nekochan_suggest/query.py`）
- [X] T011 [P] `nekochan_suggest/annotations.py` の新規・変更した全シンボルと `nekochan_suggest/cli.py` の `_handle_build_annotations` に日本語 docstring を追加する（`nekochan_suggest/annotations.py`、`nekochan_suggest/cli.py`）
- [X] T012 [P] `uv run pytest --cov=nekochan_suggest --cov-report=term-missing -m "not integration"` を実行し、`nekochan_suggest/annotations.py` の行カバレッジが ≥ 80% であることを確認する。不足がある場合は補完テストを `tests/test_annotations.py` に追加する
- [X] T013 `nekochan-suggest build-annotations --dry-run` の手動検証を実施する。Ollama (`qwen3.5:2b`) が稼働しインターネット接続がある状態で実行し、stdout に先頭 3 件のアノテーション JSON が表示されること・終了コード 0 であることを確認する
- [X] T019 [P] `specs/001-nekochan-suggest/spec.md` の明確化セッション（2026-05-04）に回答を記録する。FR-007 の `qwen3.5` を `qwen3.5:2b` に修正、GIF スキップ報告・dry-run 挙動・GIF 除外の位置付け・URL 統一の決定を記録する（`specs/001-nekochan-suggest/spec.md`）
- [X] T020 [P] `specs/001-nekochan-suggest/` に実装計画書と設計ドキュメントを作成する。`plan.md`（技術コンテキスト・憲法チェック・プロジェクト構造）、`research.md`（Ollama API・GIF 方針・埋め込みモデル等 7 項目）、`data-model.md`（AnnotationRecord・外部データソース・状態遷移・設定キー）、`quickstart.md`（インストール・実行・設定ガイド）を作成する（`specs/001-nekochan-suggest/`）
- [X] T021 `tests/test_cli.py::test_cli_text_stub_response` の統合テストを修正する。このテストは「annotations.json が存在しない場合に終了コード 1 になること」を検証しているが、`~/.local/share/nekochan-suggest/annotations.json` が既に存在する環境では終了コード 0 になり FAIL する。テストをモックベースに書き換えるか、`@pytest.mark.skipif` で環境依存条件を明示する（`tests/test_cli.py`）

---

## 依存関係と実行順序

### フェーズ間依存

```
Phase 1 (T001, T002)
    ↓
Phase 2 (T003〜T007) — 並列実行可能
    ↓
Phase 3 (T008 → T009) — 順番に実行
    ↓
Phase 4 (T014〜T018) — T016 は T014・T015 完了後
    ↓
Phase 5 (T010〜T013, T019〜T021) — T013・T021 以外は並列可能
```

### 並列実行例（US2 内）

```bash
# Phase 2: テストを全並列で記述
T003 & T004 & T005 & T006 & T007

# Phase 4: T014・T015 を並列、T016 はその後
T014 & T015 → T016 → T017 & T018

# Phase 5: 品質タスクを並列
T010 & T011 & T012 & T019 & T020
```

---

## 進捗サマリー

| フェーズ | タスク数 | 完了 | 残り |
|---------|---------|------|------|
| Phase 1: セットアップ | 2 | 2 | 0 |
| Phase 2: 基盤（TDD RED） | 5 | 5 | 0 |
| Phase 3: US2 実装 | 2 | 2 | 0 |
| Phase 4: マルチモーダル拡張 | 5 | 5 | 0 |
| Phase 5: 仕上げ | 7 | 7 | 0 |
| **合計** | **21** | **21** | **0** |

**全タスク完了** ✅
