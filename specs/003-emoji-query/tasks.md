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

**目的**: `sentence-transformers` PyPI パッケージ追加とテスト用フィクスチャファイルの準備

- [x] T001 `uv add sentence-transformers` で `sentence-transformers` PyPI 依存を追加し、`uv add --dev pytest-cov` でカバレッジ計測ツールを開発依存に追加する。`pyproject.toml` と `uv.lock` が更新されていることを確認する
- [x] T002 [P] `tests/fixtures/annotations.json` を作成する。`name: str`・`annotation: str`・`embedding: list[float]`（768 次元）を持つ正常レコードを 5 件以上、`embedding` フィールドが欠損したレコードを 1 件以上含める（スキップ動作のテスト用）（`tests/fixtures/annotations.json`）

---

## Phase 2: 基盤実装（ブロッキング前提条件）

**目的**: `SuggestionResult` dataclass の定義 — テストと実装の両方が参照するため US1 着手前に必須

**⚠️ 重要**: このフェーズが完了するまで US1 のいかなる作業も開始してはならない

- [ ] T003 `nekochan_suggest/query.py` を書き直す。事前に `grep -r 'search_similar\|embed_text' nekochan_suggest/ tests/` を実行して既存の参照がないことを確認してから、既存の `NotImplementedError` スタブ（`embed_text`・`search_similar`・旧 `suggest`）をすべて削除する。`SuggestionResult` dataclass（`name: str`・`score: float`）と正しいシグネチャを持つ `suggest(text: str, count: int = 3) -> list[SuggestionResult]` スタブ（`raise NotImplementedError`）を定義する。モジュール先頭の日本語 docstring は保持する（`nekochan_suggest/query.py`）

**チェックポイント**: `from nekochan_suggest.query import SuggestionResult, suggest` がエラーなく実行できる

## Phase 3: ユーザーストーリー 1 — 文章に合うネコチャン絵文字のファイル名を提案（優先度: P1）🎯 MVP

**目標**: ユーザーが `nekochan-suggest "テキスト"` を実行すると、コサイン類似度に基づいた絵文字候補リストが stdout に表示される

**独立テスト**:
```bash
nekochan-suggest "今日もいい天気ですね"
# → 3 件のファイル名 + スコアが stdout に表示（アノテーションファイルが利用可能な環境）
```

### ユーザーストーリー 1 のテスト（TDD — RED フェーズ: 先に記述し、FAIL を確認してから実装へ）

> **⚠️ 注意: T004〜T009 はすべて FAIL することを確認してから T010 以降の実装に進むこと**

- [ ] T004 [P] [US1] `tests/test_query.py` に `_cosine_similarity()` の単体テストを記述する。同一ベクトル → 1.0、直交ベクトル → 0.0、ゼロベクトルの 0 除算ガード → 0.0、既知のドット積による期待値検証（`tests/test_query.py`）
- [ ] T005 [P] [US1] `tests/test_query.py` に `_load_annotations()` の単体テストを記述する。`tests/fixtures/annotations.json` の正常読み込み、ファイル不在 → `FileNotFoundError`、`embedding` フィールド欠損レコードのスキップ、`embedding` が空リストのレコードのスキップ（`tests/test_query.py`）
- [ ] T006 [P] [US1] `tests/test_query.py` に `_embed_text()` の単体テストを `unittest.mock.patch('sentence_transformers.SentenceTransformer')` でモックして記述する。正常レスポンスで `list[float]` を返すこと、モデルロード失敗（`OSError`）の伝播、`RuntimeError` の伝播、`encode()` 結果が空 → `ValueError` を raise すること（`tests/test_query.py`）
- [ ] T007 [P] [US1] `tests/test_query.py` に `suggest()` の結合テストをモックした `SentenceTransformer` で記述する。デフォルト count=3 で 3 件返ること、count=2 で 2 件返ること、count がアノテーション件数を超える場合はエラーなく全件返ること（stderr への出力がないことも確認）、結果リストがスコア降順でソートされていること（`tests/test_query.py`）
- [ ] T008 [P] [US1] `tests/test_query.py` に `suggest()` のバリデーションテストを記述する。空文字列（`""`）→ `ValueError`、空白のみ（`"   "`）→ `ValueError`（strip 後に空と判定）、1001 文字テキスト → `ValueError`、`count=0` → `ValueError`、`count=11` → `ValueError`、`count=1` は通過、`count=10` は通過（`tests/test_query.py`）
- [ ] T009 [P] [US1] `tests/test_cli.py` に `_handle_query()` のテストを `unittest.mock.patch('nekochan_suggest.cli.suggest')` でモックして記述する。正常系: テキスト出力フォーマット `N. name  score:.2f`（スコア小数点以下 2 桁固定・ファイル名とスコアの間はスペース 2 つ）、`--json` 出力が `{"suggestions": [{"name": str, "score": float}]}` に一致する有効な JSON であること（`score` 値は丸めなし）、`--count 5` で `suggest` が `count=5` で呼び出されること、CLI 引数と stdin が同時指定された場合は CLI 引数が優先されること（FR-008）。エラー経路（mock side_effect）: 空テキスト → stderr `"Error: text is empty."` 終了コード 1、空白のみテキスト → stderr `"Error: text is empty."` 終了コード 1、1001 文字テキスト → stderr `"Error: text is too long (max 1000 characters)."` 終了コード 1、`count=0` → stderr `"Error: --count out of range (1-10)."` 終了コード 1、`count=11` → stderr `"Error: --count out of range (1-10)."` 終了コード 1、アノテーションファイル不在（`FileNotFoundError`）→ stderr `"Error: annotations file not found. Run 'nekochan-suggest build-annotations' first."` 終了コード 1。TTY stdin エラー経路（`sys.stdin.isatty()` 確認）と stdin パイプ正常系（`echo "おはよう" | nekochan-suggest` → 終了コード 0・候補 3 件が stdout に出力される）は `subprocess.run` を使用し **`@pytest.mark.integration` マーカーを付与する**（CI では `pytest -m "not integration"` でスキップ）（`tests/test_cli.py`）

### ユーザーストーリー 1 の実装

- [ ] T010 [US1] `nekochan_suggest/query.py` に `_cosine_similarity(a: list[float], b: list[float]) -> float` と `_load_annotations(path: Path) -> list[dict]` を実装する。`math` 標準ライブラリのみを使用し numpy 禁止、`embedding` が欠損または空のレコードはスキップする。アノテーションファイルが存在しない場合は `FileNotFoundError` を raise する（`nekochan_suggest/query.py`）
- [ ] T011 [US1] `nekochan_suggest/query.py` に `_load_config() -> dict` を実装する。`tomllib` で `~/.config/nekochan-suggest/config.toml` を読み込む（ファイル不在の場合は `{}` を返す）。`embed_model`・`llm_model` を優先順位: 環境変数（`NEKOCHAN_EMBED_MODEL`・`NEKOCHAN_LLM_MODEL`）> config.toml（`embed_model`・`llm_model` キー）> デフォルト値（`intfloat/multilingual-e5-base`・`qwen3.5`）で解決し、すべてのキーを dict で返す（`nekochan_suggest/query.py`）
- [ ] T012 [US1] `nekochan_suggest/query.py` に `_embed_text(text: str, embed_model: str) -> list[float]` を実装する。`sentence_transformers.SentenceTransformer(embed_model).encode("query: " + text)` を使用し（非対称検索プレフィックス: クエリ側は `"query: "`）、`.tolist()` で `list[float]` に変換する。`encode()` 結果が空または次元数が 0 の場合は `ValueError` を raise する。`OSError`・`RuntimeError`・`ValueError` は呼び出し元に伝播する。ライブラリコード内では `print()` を使わず `logging` を使用する（`nekochan_suggest/query.py`）
- [ ] T013 [US1] `nekochan_suggest/query.py` に `suggest(text: str, count: int = 3) -> list[SuggestionResult]` を実装する。入力バリデーション（strip 後に 1〜1000 文字・count 1〜10）、`_load_config()` による `embed_model` 設定読み込み、`~/.local/share/nekochan-suggest/annotations.json` からのアノテーション読み込み（`_load_annotations()`）、テキストの埋め込み変換（`_embed_text(text, embed_model)`）、全レコードとのコサイン類似度計算（`_cosine_similarity()`）、上位 N 件をスコア降順で返す。count がアノテーション件数を超える場合は利用可能な全件を返す（エラーなし・警告なし）。ライブラリ内では `print()` を使わず `logging` でデバッグ・エラーイベントを記録する（`nekochan_suggest/query.py`）
- [ ] T014 [US1] `nekochan_suggest/cli.py` の `_handle_query(args: argparse.Namespace) -> None` を完成させる。①入力解決: `args.text` がある場合は CLI 引数を使用し stdin を無視する（FR-008・CLI 引数優先）；`args.text` がない場合は `sys.stdin.isatty()` を確認し、非 TTY なら `sys.stdin.read().strip()` から取得、TTY なら `"Error: provide text as an argument or pipe it via stdin."` を stderr に出力して終了コード 1 で終了する（既存の日本語 TTY エラーメッセージがあれば英語版に置き換える）。②バリデーション: 空テキスト → `"Error: text is empty."`、1000 文字超 → `"Error: text is too long (max 1000 characters)."`、`count` が 1〜10 範囲外 → `"Error: --count out of range (1-10)."` をそれぞれ stderr に出力して終了コード 1。③初回モデルダウンロード通知: `suggest()` 呼び出し前に `embed_model` のキャッシュ有無を確認し（`sentence_transformers` のキャッシュディレクトリ存在確認等）、未キャッシュの場合は `"Downloading model <model_name>..."` を stderr に 1 行出力する（FR-012）。④`suggest()` を `try/except` で呼び出し、成功時は `N. name  score:.2f` テキスト（スペース 2 つ区切り）または `{"suggestions":[...]}` JSON（score は丸めなし生の浮動小数点）を stdout に出力して終了コード 0。⑤例外処理: `FileNotFoundError` → `"Error: annotations file not found. Run 'nekochan-suggest build-annotations' first."`、`OSError` → `"Error: failed to load embedding model '{model}'."`、`RuntimeError` → `"Error: embedding failed: {message}"`、埋め込み異常の `ValueError` → `"Error: unexpected embedding result. Check embed_model setting."` をそれぞれ stderr に出力して終了コード 1（`nekochan_suggest/cli.py`）
- [ ] T015 [P] [US1] `nekochan_suggest/query.py` と `nekochan_suggest/cli.py` のすべての公開・非公開シンボルに完全な型アノテーションを付与する。`pyrefly nekochan_suggest/` を実行し、報告されたエラーをすべて修正する（`nekochan_suggest/query.py`、`nekochan_suggest/cli.py`）
- [ ] T016 [P] [US1] `nekochan_suggest/query.py`（`SuggestionResult`・`suggest` および内部関数）と `nekochan_suggest/cli.py`（`_handle_query`）の新規・変更した全シンボルに日本語 docstring を追加する。`query.py` 内に `print()` 呼び出しが残っていないことを確認する（`nekochan_suggest/query.py`、`nekochan_suggest/cli.py`）

**チェックポイント**: `nekochan-suggest "おはよう"` が 3 件の候補を返す。T004–T016 の全テストがパス。`pytest --cov` で `query.py` と `cli.py` のカバレッジ ≥ 80%

---

## Phase 4: 仕上げ・横断的関心事

**目的**: カバレッジ確認・型チェック・クイックスタート検証

- [ ] T017 [P] `pytest --cov=nekochan_suggest --cov-report=term-missing` を実行し、`nekochan_suggest/query.py` と `nekochan_suggest/cli.py` の行カバレッジが ≥ 80% であることを確認する。不足がある場合は補完テストを `tests/test_query.py` または `tests/test_cli.py` に追加する
- [ ] T018 [P] `pyrefly nekochan_suggest/` を厳格モードで実行し、`query.py` と `cli.py` の残存型エラーをすべて解消する（`nekochan_suggest/query.py`、`nekochan_suggest/cli.py`）
- [ ] T019 `specs/003-emoji-query/quickstart.md` の手動検証を実施する。`sentence-transformers` がインストール済みの状態で quickstart.md 内の各コマンド例（基本呼び出し・stdin パイプ・`--count`・`--json`・エラー系）を実行し、出力がドキュメントの期待値と一致することを確認する
- [ ] T020 SC-002 手動精度検証: `specs/003-emoji-query/checklists/requirements.md` にポジティブ・ネガティブ・眠い・元気・ニュートラルのトーンをカバーする 5 件の検証クエリと期待ファイル名を定義する。各クエリで `nekochan-suggest` を実行し、期待するファイル名が候補上位 3 件に含まれることを確認する。合格基準: 5 件中 4 件以上（≥ 80%）。結果をチェックリストに記録する（`specs/003-emoji-query/checklists/requirements.md`）

---

## 依存関係と実行順序

### フェーズ間依存

- **セットアップ（Phase 1）**: 依存なし — 即座に開始可能。T001 と T002 は独立して並列実行可 [P]（両タスク完了済み ✅）
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
Phase 1:  T001 ✅ ║ T002 ✅
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

1. T001–T002 完了後（完了済み ✅）: 依存関係確定、テストフィクスチャ利用可
2. T003 完了後: `SuggestionResult` がインポート可能、スタブ API 確定
3. T004–T009 完了後（RED）: テストスイートが意図どおり FAIL → TDD ベースライン確立
4. T010 完了後: `_cosine_similarity` + `_load_annotations` がグリーン
5. T011 完了後: 設定解決ロジック（`_load_config`）がグリーン
6. T012 完了後: `_embed_text`（モック）がグリーン
7. T013 完了後: `suggest()` エンドツーエンド（モック）がグリーン — ライブラリ API 完成
8. T014 完了後: CLI 統合（stdin 優先順位・初回 DL 通知・全エラーパス）がグリーン — **機能完成**
9. T015–T016 完了後: 型安全 + 日本語ドキュメント完備
10. T017–T020 完了後: カバレッジ確認 + 手動検証完了 — **フィーチャー完了**
