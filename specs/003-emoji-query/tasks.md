# Tasks: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**Input**: Design documents from `/specs/003-emoji-query/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli.md ✅, quickstart.md ✅
**TDD**: 憲法原則 II に従い、すべての実装タスクの前にテストを先に記述する（RED → GREEN）

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 並列実行可能（別ファイル・完了待ち依存なし）
- **[US1]**: ユーザーストーリー 1（本フィーチャーの唯一のストーリー）
- タスクにはすべて正確なファイルパスを含む

---

## Phase 1: Setup（依存関係とテストインフラ）

**目的**: `ollama` PyPI パッケージ追加とテスト用フィクスチャファイルの準備

- [ ] T001 Add `ollama` PyPI dependency with `uv add ollama` and verify `pyproject.toml` and `uv.lock` are updated
- [ ] T002 [P] Create `tests/fixtures/annotations.json` with ≥5 dummy records (each having `name: str`, `annotation: str`, `embedding: list[float]` with 768 dimensions) plus ≥1 record missing `embedding` field for skip-test coverage

---

## Phase 2: Foundational（ブロッキング前提条件）

**目的**: `SuggestionResult` dataclass の定義 — テストと実装の両方が参照するため US1 着手前に必須

**⚠️ CRITICAL**: このフェーズが完了するまで US1 のいかなる作業も開始してはならない

- [ ] T003 Rewrite `nekochan_suggest/query.py`: remove all existing `NotImplementedError` stubs (`embed_text`, `search_similar`, old `suggest`), define `SuggestionResult` dataclass (`name: str`, `score: float`) and `suggest(text, count, timeout) -> list[SuggestionResult]` stub with correct signature and `raise NotImplementedError`; preserve module-level Japanese docstring

**Checkpoint**: `from nekochan_suggest.query import SuggestionResult, suggest` がエラーなく実行できる

---

## Phase 3: User Story 1 — 文章に合うネコチャン絵文字のファイル名を提案（Priority: P1）🎯 MVP

**Goal**: ユーザーが `nekochan-suggest "テキスト"` を実行すると、コサイン類似度に基づいた絵文字候補リストが stdout に表示される

**Independent Test**:
```bash
nekochan-suggest "今日もいい天気ですね"
# → 3 件のファイル名 + スコアが stdout に表示（アノテーションファイルと Ollama が利用可能な環境）
```

### Tests for User Story 1（TDD — RED フェーズ: 先に記述し、FAIL を確認してから実装へ）

> **⚠️ NOTE: T004〜T009 はすべて FAIL することを確認してから T010 以降の実装に進むこと**

- [ ] T004 [P] [US1] Write unit tests for `_cosine_similarity()` in `tests/test_query.py`: identical vectors → 1.0, orthogonal vectors → 0.0, zero-vector → 0.0 guard, known dot-product expected value
- [ ] T005 [P] [US1] Write unit tests for `_load_annotations()` in `tests/test_query.py`: normal load from `tests/fixtures/annotations.json`, missing file → `FileNotFoundError`, record missing `embedding` field is skipped, record with empty `embedding` list is skipped
- [ ] T006 [P] [US1] Write unit tests for `_embed_text()` with `unittest.mock.patch('ollama.Client')` in `tests/test_query.py`: normal response returns `list[float]`, `ConnectionError` propagates, `ollama.ResponseError` propagates, `httpx.TimeoutException` propagates, empty `response.embeddings` → raises `ValueError`
- [ ] T007 [P] [US1] Write integration tests for `suggest()` with mocked `ollama.Client` in `tests/test_query.py`: default count=3 returns 3 results, count=2 returns 2 results, count > available entries returns all available (no error), result list is sorted by score descending
- [ ] T008 [P] [US1] Write validation tests for `suggest()` in `tests/test_query.py`: empty string (`""`) → `ValueError`, whitespace-only (`"   "`) → `ValueError`, 1001-char text → `ValueError`, `count=0` → `ValueError`, `count=11` → `ValueError`, `count=1` passes, `count=10` passes
- [ ] T009 [P] [US1] Write CLI integration tests for `_handle_query()` in `tests/test_cli.py` (using `subprocess.run` or `unittest.mock`): text output format `N. name  score:.2f`, `--json` output is valid JSON matching `{"suggestions": [{"name": str, "score": float}]}`, `--count 5` returns 5 lines, empty-text → stderr `"Error: text is empty."` exit 1, 1001-char text → stderr `"Error: text is too long..."` exit 1, annotations file missing → stderr `"Error: annotations file not found..."` exit 1, `NEKOCHAN_TIMEOUT=abc` → stderr `"Error: NEKOCHAN_TIMEOUT must be a positive integer."` exit 1, `NEKOCHAN_TIMEOUT=60` with no `--timeout` uses 60, `--timeout` overrides `NEKOCHAN_TIMEOUT`

### Implementation for User Story 1

- [ ] T010 [US1] Implement `_cosine_similarity(a: list[float], b: list[float]) -> float` and `_load_annotations(path: Path) -> list[dict]` in `nekochan_suggest/query.py`: use `math` stdlib only; skip records with missing or empty `embedding`; raise `FileNotFoundError` if annotations file absent
- [ ] T011 [US1] Implement `_load_config() -> dict` in `nekochan_suggest/query.py`: read `~/.config/nekochan-suggest/config.toml` with `tomllib` (return `{}` if file absent); resolve `ollama_url` and `embed_model` with priority env var (`NEKOCHAN_OLLAMA_URL`, `NEKOCHAN_EMBED_MODEL`) > config.toml > defaults (`http://localhost:11434`, `nomic-embed-text`)
- [ ] T012 [US1] Implement `_embed_text(text: str, ollama_url: str, embed_model: str, timeout: int) -> list[float]` in `nekochan_suggest/query.py`: use `ollama.Client(host=ollama_url, timeout=timeout).embed(model=embed_model, input=text)`; validate `response.embeddings` non-empty; propagate `ConnectionError`, `ollama.ResponseError`, `httpx.TimeoutException`, `ValueError` to caller
- [ ] T013 [US1] Implement `suggest(text: str, count: int = 3, timeout: int = 30) -> list[SuggestionResult]` in `nekochan_suggest/query.py`: validate inputs (strip text, 1–1000 chars, count 1–10); load config via `_load_config()`; load annotations from `~/.local/share/nekochan-suggest/annotations.json`; embed text; compute cosine similarity for all records; return top-N sorted descending; add `logging` calls for debug and error events (no `print()` in library)
- [ ] T014 [US1] Complete `_handle_query(args: argparse.Namespace) -> None` in `nekochan_suggest/cli.py`: resolve timeout (priority: `--timeout` > `NEKOCHAN_TIMEOUT` env var > default 30; validate `NEKOCHAN_TIMEOUT` is positive integer or stderr exit 1); resolve stdin pipe (non-TTY only; TTY without text → stderr exit 1); validate text and count or stderr exit 1; call `suggest()` inside `try/except`; on success format output (`N. name  score:.2f` text or `{"suggestions":[...]}` JSON to stdout exit 0); on `FileNotFoundError` → `"Error: annotations file not found. Run 'nekochan-suggest build-annotations' first."` stderr exit 1; on `ConnectionError` → `"Error: cannot connect to Ollama at {url}. Make sure Ollama is running."` stderr exit 1; on `ollama.ResponseError` → `"Error: Ollama returned an error: {message}"` stderr exit 1; on `TimeoutException` → `"Error: request timed out after {N} seconds."` stderr exit 1; on `ValueError` (unexpected embeddings) → `"Error: unexpected response from Ollama. Check if 'ollama pull {model}' was run."` stderr exit 1
- [ ] T015 [P] [US1] Add complete type annotations to all public and private symbols in `nekochan_suggest/query.py` and `nekochan_suggest/cli.py`; run `pyrefly nekochan_suggest/` and fix all reported errors
- [ ] T016 [P] [US1] Add Japanese docstrings to all new and modified public symbols in `nekochan_suggest/query.py` (`SuggestionResult`, `suggest`) and `nekochan_suggest/cli.py` (`_handle_query`); verify no `print()` calls remain in `query.py`

**Checkpoint**: `nekochan-suggest "おはよう"` が 3 件の候補を返す。T004–T016 の全テストがパス。`pytest --cov` で `query.py` と `cli.py` のカバレッジ ≥ 80%

---

## Phase 4: Polish & Cross-Cutting Concerns

**目的**: カバレッジ確認・型チェック・クイックスタート検証

- [ ] T017 [P] Run `pytest --cov=nekochan_suggest --cov-report=term-missing` and confirm line coverage ≥ 80% for `nekochan_suggest/query.py` and `nekochan_suggest/cli.py`; fix gaps if needed
- [ ] T018 [P] Run `pyrefly nekochan_suggest/` in strict mode and resolve any remaining type errors across `query.py` and `cli.py`
- [ ] T019 Run quickstart.md manual validation: execute each example command in `specs/003-emoji-query/quickstart.md` with Ollama running locally and `nomic-embed-text` pulled; verify all outputs match documented examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし — 即座に開始可能。T001 と T002 は独立して並列実行可 [P]
- **Foundational (Phase 2)**: Phase 1 完了後 — T003 は T001（pyproject.toml 更新）に依存
- **User Story 1 (Phase 3)**: Phase 2 完了後
  - **RED フェーズ** (T004–T009): T003（SuggestionResult）と T002（フィクスチャ）完了後、すべて並列実行可 [P]
  - **GREEN フェーズ** (T010–T016): 順次実装
    - T010 → T011 → T012 → T013（query.py の積み上げ）
    - T014（cli.py、T013 のインターフェース確定後）
    - T015・T016 は T013 + T014 完了後に並列実行可 [P]
- **Polish (Phase 4)**: Phase 3 全タスク完了後。T017 と T018 は並列実行可 [P]。T019 は T017+T018 の後

### US1 内の並列実行チャート

```
Phase 1:  T001 ║ T002
               ↓
Phase 2:  T003
               ↓
RED:   T004 ║ T005 ║ T006 ║ T007 ║ T008 ║ T009   (全並列)
               ↓ (confirm all FAIL)
GREEN: T010 → T011 → T012 → T013
                                  → T014
                                  T015 ║ T016   (T013+T014 後に並列)
               ↓
Polish:   T017 ║ T018
               ↓
          T019
```

### ユーザーストーリー内の依存関係

本フィーチャーはユーザーストーリーが 1 つのみのため、ストーリー間の依存はない。

---

## Implementation Strategy

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
10. T017–T019 完了後: カバレッジ確認 + クイックスタート検証 — **フィーチャー完了**
