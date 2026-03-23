# タスクリスト: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**入力**: `/specs/003-emoji-query/` 配下の設計ドキュメント群  
**前提条件**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli.md ✅, quickstart.md ✅  
**TDD**: 憲法原則 II に従い、すべての実装タスクの前にテストを先に記述する（RED → GREEN）

## 表記: `[ID] [P?] [US?] 説明`

- **[P]**: 並列実行可能（別ファイル・完了待ち依存なし）
- **[US1]**: ユーザーストーリー 1（本フィーチャーの唯一のストーリー）
- タスクにはすべて正確なファイルパスを含む

---

## Phase 1: セットアップ（依存関係とテストインフラ）

**目的**: `ollama` PyPI パッケージ追加とテスト用フィクスチャファイルの準備

- [ ] T001 `uv add ollama` で `ollama` PyPI 依存を追加し、`uv add --dev pytest-cov` でカバレッジ計測ツールを開発依存に追加する。注意: `httpx` は `ollama` の間接依存であり、テスト（T006）では `import httpx` で直接インポートするが pyproject.toml への追加は不要。`pyproject.toml` と `uv.lock` が更新されていることを確認する
- [ ] T002 [P] `tests/fixtures/annotations.json` を作成する。`name: str`・`annotation: str`・`embedding: list[float]`（768 次元）を持つ正常レコードを 5 件以上、`embedding` フィールドが欠損したレコードを 1 件以上含める（スキップ動作のテスト用）

---

## Phase 2: 基盤実装（ブロッキング前提条件）

**目的**: `SuggestionResult` dataclass の定義 — テストと実装の両方が参照するため US1 着手前に必須

**⚠️ 重要**: このフェーズが完了するまで US1 のいかなる作業も開始してはならない

- [ ] T003 `nekochan_suggest/query.py` を書き直す。事前に `grep -r 'search_similar\|embed_text' nekochan_suggest/ tests/` を実行して既存の参照がないことを確認してから、既存の `NotImplementedError` スタブ（`embed_text`・`search_similar`・旧 `suggest`）をすべて削除する。`SuggestionResult` dataclass（`name: str`・`score: float`）と正しいシグネチャを持つ `suggest(text, count, timeout) -> list[SuggestionResult]` スタブ（`raise NotImplementedError`）を定義する。モジュール先頭の日本語 docstring は保持する

**チェックポイント**: `from nekochan_suggest.query import SuggestionResult, suggest` がエラーなく実行できる

---

## Phase 3: ユーザーストーリー 1 — 文章に合うネコチャン絵文字のファイル名を提案（優先度: P1）🎯 MVP

**目標**: ユーザーが `nekochan-suggest "テキスト"` を実行すると、コサイン類似度に基づいた絵文字候補リストが stdout に表示される

**独立テスト**:
```bash
nekochan-suggest "今日もいい天気ですね"
# → 3 件のファイル名 + スコアが stdout に表示（アノテーションファイルと Ollama が利用可能な環境）
```

### ユーザーストーリー 1 のテスト（TDD — RED フェーズ: 先に記述し、FAIL を確認してから実装へ）

> **⚠️ 注意: T004〜T009 はすべて FAIL することを確認してから T010 以降の実装に進むこと**

- [ ] T004 [P] [US1] `tests/test_query.py` に `_cosine_similarity()` の単体テストを記述する。同一ベクトル → 1.0、直交ベクトル → 0.0、ゼロベクトルの 0 除算ガード → 0.0、既知のドット積による期待値検証
- [ ] T005 [P] [US1] `tests/test_query.py` に `_load_annotations()` の単体テストを記述する。`tests/fixtures/annotations.json` の正常読み込み、ファイル不在 → `FileNotFoundError`、`embedding` フィールド欠損レコードのスキップ、`embedding` が空リストのレコードのスキップ
- [ ] T006 [P] [US1] `tests/test_query.py` に `_embed_text()` の単体テストを `unittest.mock.patch('ollama.Client')` でモックして記述する。正常レスポンスで `list[float]` を返すこと、`ConnectionError` の伝播、`ollama.ResponseError` の伝播、`httpx.TimeoutException` の伝播、`response.embeddings` が空 → `ValueError` を raise すること
- [ ] T007 [P] [US1] `tests/test_query.py` に `suggest()` の結合テストをモックした `ollama.Client` で記述する。デフォルト count=3 で 3 件返ること、count=2 で 2 件返ること、count がアノテーション件数を超える場合はエラーなく全件返ること（stderr への出力がないことも確認する）、結果リストがスコア降順でソートされていること
- [ ] T008 [P] [US1] `tests/test_query.py` に `suggest()` のバリデーションテストを記述する。空文字列（`""`）→ `ValueError`、空白のみ（`"   "`）→ `ValueError`、1001 文字テキスト → `ValueError`、`count=0` → `ValueError`、`count=11` → `ValueError`、`count=1` は通過、`count=10` は通過
- [ ] T009 [P] [US1] `tests/test_cli.py` に `_handle_query()` のテストを `unittest.mock.patch('nekochan_suggest.cli.suggest')` でモックして記述する。正常系: テキスト出力フォーマット `N. name  score:.2f`、`--json` 出力が `{"suggestions": [{"name": str, "score": float}]}` に一致する有効な JSON であること、`--count 5` で suggest が count=5 で呼び出されること。エラー経路（mock side_effect）: 空テキスト → stderr `"Error: text is empty."` 終了コード 1、1001 文字テキスト → stderr `"Error: text is too long (max 1000 characters)."` 終了コード 1、アノテーションファイル不在（`FileNotFoundError`）→ stderr `"Error: annotations file not found. Run 'nekochan-suggest build-annotations' first."` 終了コード 1、`NEKOCHAN_TIMEOUT=abc` → stderr `"Error: NEKOCHAN_TIMEOUT must be a positive integer."` 終了コード 1、`NEKOCHAN_TIMEOUT=60` かつ `--timeout` 未指定で suggest に timeout=60 が渡ること、`--timeout 10` が `NEKOCHAN_TIMEOUT` より優先されること。TTY stdin エラー経路（`sys.stdin.isatty()` 確認）と stdin パイプ正常系（`echo "おはよう" | nekochan-suggest` → 終了コード 0・候補 3 件が stdout に出力される）は `subprocess.run` を使用する

### ユーザーストーリー 1 の実装

- [ ] T010 [US1] `nekochan_suggest/query.py` に `_cosine_similarity(a: list[float], b: list[float]) -> float` と `_load_annotations(path: Path) -> list[dict]` を実装する。`math` 標準ライブラリのみを使用し、`embedding` が欠損または空のレコードはスキップする。アノテーションファイルが存在しない場合は `FileNotFoundError` を raise する
- [ ] T011 [US1] `nekochan_suggest/query.py` に `_load_config() -> dict` を実装する。`tomllib` で `~/.config/nekochan-suggest/config.toml` を読み込む（ファイル不在の場合は `{}` を返す）。`ollama_url`・`embed_model`・`llm_model` を優先順位: 環境変数（`NEKOCHAN_OLLAMA_URL`・`NEKOCHAN_EMBED_MODEL`・`NEKOCHAN_LLM_MODEL`）> config.toml > デフォルト値（`http://localhost:11434`・`nomic-embed-text`・`qwen3.5`）で解決し、本フィーチャーで未使用のキーも含めてすべて dict で返す（FR-013 に基づき将来の build-annotations フィーチャーとの一貫性を確保するため）
- [ ] T012 [US1] `nekochan_suggest/query.py` に `_embed_text(text: str, ollama_url: str, embed_model: str, timeout: int) -> list[float]` を実装する。`ollama.Client(host=ollama_url, timeout=timeout).embed(model=embed_model, input=text)` を使用し、`response.embeddings` が空でないことを検証する。`ConnectionError`・`ollama.ResponseError`・`httpx.TimeoutException`・`ValueError` は呼び出し元に伝播する
- [ ] T013 [US1] `nekochan_suggest/query.py` に `suggest(text: str, count: int = 3, timeout: int = 30) -> list[SuggestionResult]` を実装する。入力バリデーション（strip 後に 1〜1000 文字・count 1〜10）、`_load_config()` による設定読み込み、`~/.local/share/nekochan-suggest/annotations.json` からのアノテーション読み込み、テキストの埋め込み変換、全レコードとのコサイン類似度計算、上位 N 件をスコア降順で返す。ライブラリコード内では `print()` を使わず `logging` でデバッグ・エラーイベントを記録する
- [ ] T014 [US1] `nekochan_suggest/cli.py` の `_handle_query(args: argparse.Namespace) -> None` を完成させる。タイムアウト解決（優先順位: `--timeout` > `NEKOCHAN_TIMEOUT` 環境変数 > config.toml の `timeout` キー > デフォルト 30；`NEKOCHAN_TIMEOUT` が正の整数でない場合は stderr 出力して終了コード 1）、stdin パイプ解決（非 TTY のみ；TTY でテキスト未指定の場合は `"Error: provide text as an argument or pipe it via stdin."` を stderr に出力して終了コード 1；既存の日本語 TTY エラーメッセージをこの英語版に置き換える（FR-006 準拠））、テキストと count のバリデーション（失敗時は stderr 出力して終了コード 1）、`suggest()` を `try/except` で呼び出し、成功時は `N. name  score:.2f` テキストまたは `{"suggestions":[...]}` JSON を stdout に出力して終了コード 0。例外処理: `FileNotFoundError` → `"Error: annotations file not found. Run 'nekochan-suggest build-annotations' first."`、`ConnectionError` → `"Error: cannot connect to Ollama at {url}. Make sure Ollama is running."`、`ollama.ResponseError` → `"Error: Ollama returned an error: {message}"`、`TimeoutException` → `"Error: request timed out after {N} seconds."`、`ValueError`（埋め込み異常）→ `"Error: unexpected response from Ollama. Check if 'ollama pull {model}' was run."` をそれぞれ stderr に出力して終了コード 1
- [ ] T015 [P] [US1] `nekochan_suggest/query.py` と `nekochan_suggest/cli.py` のすべての公開・非公開シンボルに完全な型アノテーションを付与する。`pyrefly nekochan_suggest/` を実行し、報告されたエラーをすべて修正する
- [ ] T016 [P] [US1] `nekochan_suggest/query.py`（`SuggestionResult`・`suggest`）と `nekochan_suggest/cli.py`（`_handle_query`）の新規・変更した公開シンボルすべてに日本語 docstring を追加する。`query.py` 内に `print()` 呼び出しが残っていないことを確認する

**チェックポイント**: `nekochan-suggest "おはよう"` が 3 件の候補を返す。T004–T016 の全テストがパス。`pytest --cov` で `query.py` と `cli.py` のカバレッジ ≥ 80%

---

## Phase 4: 仕上げ・横断的関心事

**目的**: カバレッジ確認・型チェック・クイックスタート検証

- [ ] T017 [P] `pytest --cov=nekochan_suggest --cov-report=term-missing` を実行し、`nekochan_suggest/query.py` と `nekochan_suggest/cli.py` の行カバレッジが ≥ 80% であることを確認する。不足がある場合は補完する
- [ ] T018 [P] `pyrefly nekochan_suggest/` を厳格モードで実行し、`query.py` と `cli.py` の残存型エラーをすべて解消する
- [ ] T019 `specs/003-emoji-query/quickstart.md` の手動検証を実施する。Ollama をローカルで起動し `nomic-embed-text` をプルした状態で、quickstart.md 内の各コマンド例を実行して出力がドキュメントの期待値と一致することを確認する
- [ ] T020 SC-002 手動精度検証: `specs/003-emoji-query/checklists/requirements.md` にポジティブ・ネガティブ・眠い・元気・ニュートラルのトーンをカバーする 5 件の検証クエリと期待ファイル名を定義する。各クエリで `nekochan-suggest` を実行し、期待するファイル名が候補上位 3 件に含まれることを確認する。合格基準: 5 件中 4 件以上（≥80%）。結果をチェックリストに記録する

---

## 依存関係と実行順序

### フェーズ間依存

- **セットアップ（Phase 1）**: 依存なし — 即座に開始可能。T001 と T002 は独立して並列実行可 [P]
- **基盤実装（Phase 2）**: Phase 1 完了後 — T003 は T001（pyproject.toml 更新）に依存
- **ユーザーストーリー 1（Phase 3）**: Phase 2 完了後
  - **RED フェーズ**（T004–T009）: T003（SuggestionResult）と T002（フィクスチャ）完了後、すべて並列実行可 [P]
  - **GREEN フェーズ**（T010–T016）: 順次実装
    - T010 → T011 → T012 → T013（query.py の積み上げ）
    - T014（cli.py、T013 のインターフェース確定後）
    - T015・T016 は T013 + T014 完了後に並列実行可 [P]
- **仕上げ（Phase 4）**: Phase 3 全タスク完了後。T017 と T018 は並列実行可 [P]。T019 は T017+T018 の後

### US1 内の並列実行チャート

```
Phase 1:  T001 ║ T002
               ↓
Phase 2:  T003
               ↓
RED:   T004 ║ T005 ║ T006 ║ T007 ║ T008 ║ T009   (全並列)
               ↓ （全 FAIL を確認）
GREEN: T010 → T011 → T012 → T013
                                  → T014
                                  T015 ║ T016   (T013+T014 後に並列)
               ↓
仕上げ:   T017 ║ T018
               ↓
          T019 → T020
```

### ユーザーストーリー内の依存関係

本フィーチャーはユーザーストーリーが 1 つのみのため、ストーリー間の依存はない。

---

## 実装ストラテジー

**MVP スコープ**: このフィーチャー唯一のストーリーが P1 のため、Phase 1〜Phase 3 全体が MVP

**インクリメンタル・デリバリー**:

1. T001–T002 完了後: 依存関係確定、テストフィクスチャ利用可
2. T003 完了後: `SuggestionResult` がインポート可能、スタブ API 確定
3. T004–T009 完了後（RED）: テストスイートが意図どおり FAIL → TDD ベースライン確立
4. T010 完了後: `_cosine_similarity` + `_load_annotations` がグリーン
5. T011 完了後: 設定解決ロジックがグリーン
6. T012 完了後: `_embed_text`（モック）がグリーン
7. T013 完了後: `suggest()` エンドツーエンド（モック）がグリーン — ライブラリ API 完成
8. T014 完了後: CLI 統合がグリーン — **機能完成**
9. T015–T016 完了後: 型安全 + 日本語ドキュメント完備
10. T017–T020 完了後: カバレッジ確認 + 手動検証完了 — **フィーチャー完了**
