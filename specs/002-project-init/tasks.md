# タスク: プロジェクト初期化

**Input**: `/specs/002-project-init/` の設計文書一式  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/cli.md ✅

**テストについて**: 憲法 原則 II（テストファースト）に従い、T007 のテスト作成を US1 実装（T003・T004）の前に配置する。テストは最初に赤状態（FAIL）であることを確認してから実装に進む。

## フォーマット: `[ID] [P?] [Story?] 説明`

- **[P]**: 並行実行可能（異なるファイル、未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー（US1〜US4）
- 各タスクに正確なファイルパスを記載

---

## Phase 1: セットアップ（共有基盤）

**目的**: パッケージ定義と依存関係の設定。すべてのユーザーストーリーの前提条件。

- [ ] T001 pyproject.toml を作成する（パッケージ名・Python 3.11+ 要件・エントリーポイント 2 件・依存グループ・pytest 基本設定）`pyproject.toml`
- [ ] T002 [P] nekochan_suggest/__init__.py を作成する（パッケージバージョン定義・日本語 docstring）`nekochan_suggest/__init__.py`

**チェックポイント**: `uv sync` がエラーなく完了し、仮想環境が作成されること

---

## Phase 2: US1 — 開発者がリポジトリをクローンしてすぐに動作確認できる（優先度: P1）🎯 MVP

**Goal**: `nekochan-suggest --help` と `nekochan-suggest-ui --help` が正常に動作する状態

**独立テスト**: `uv sync` 後に `uv run nekochan-suggest --help` を実行し、
`--count`・`--json`・`--timeout` オプションを含むヘルプが表示されれば完結

### テスト（先に作成 → RED を確認してから実装へ）⚠️

- [ ] T007 [US1] tests/test_cli.py を作成する（パッケージインポート・`--help` 出力検証・`build-annotations` サブコマンド認識・終了コード 0 の基本テスト）。**作成後に `uv run pytest` を実行し、テストが FAIL することを確認してから次のタスクへ進む** `tests/test_cli.py`

### 実装

- [ ] T003 [US1] cli.py を実装する（argparse でヘルプ・テキスト位置引数・`build-annotations` サブコマンド・`--count`/`--json`/`--timeout` オプション・スタブ応答出力・型ヒント・日本語 docstring。`--json` フラグは引数として定義し、指定時は「未実装（別フィーチャーで実装予定）」のメッセージを返すスタブとする。憲法 原則 III の `--json` 必須要件への対応は plan.md Constitution Check 原則 III の正当化に基づく）`nekochan_suggest/cli.py`
- [ ] T004 [P] [US1] ui.py を実装する（`import streamlit` をモジュールトップレベルに配置し未インストール時は Python デフォルトの `ImportError` に委ねる・`main()` でプレースホルダーメッセージを出力・`--help` 対応・型ヒント・日本語 docstring）`nekochan_suggest/ui.py`

**チェックポイント**: 以下がすべて動作すること
```
uv run nekochan-suggest --help       # --count/--json/--timeout が表示される
uv run nekochan-suggest "テスト"      # プレースホルダーメッセージが表示される
uv run nekochan-suggest build-annotations  # プレースホルダーメッセージが表示される
uv run nekochan-suggest-ui --help    # GUI 説明が表示される
uv run pytest                        # T007 のテストが GREEN（PASS）になること
```

---

## Phase 3: US2 — プロジェクトのパッケージ構造が整備されている（優先度: P2）

**Goal**: 後続フィーチャーが実装を配置できる 5 モジュール構成のパッケージ骨格が存在する

**独立テスト**: `from nekochan_suggest import query, annotations` がエラーなくインポートできれば完結

- [ ] T005 [P] [US2] query.py を実装する（埋め込みベクトル検索の型ヒント付きスタブ関数・日本語 docstring）`nekochan_suggest/query.py`
- [ ] T006 [P] [US2] annotations.py を実装する（アノテーション生成・保存の型ヒント付きスタブ関数・日本語 docstring）`nekochan_suggest/annotations.py`

**チェックポイント**: `from nekochan_suggest import cli, query, annotations, ui` がすべてエラーなくインポートできること

---

## Phase 4: US4 — リント・型チェック・フォーマットを 1 コマンドで実行できる（優先度: P3）

**Goal**: `make check` 1 コマンドで lint → typecheck → test が順に実行され、すべてエラーゼロで完了する

**独立テスト**: `make check` を実行し、初期スタブコードに対してエラーゼロで完了すれば完結

- [ ] T008 [US4] pyproject.toml に ruff・pyrefly 設定を追加する（T001 で作成済みの `pyproject.toml` に追記する・`[tool.ruff]` target-version/line-length・`[tool.ruff.lint]` select=E/F/I/N/UP・`[tool.pyrefly]` project-includes）`pyproject.toml`
- [ ] T009 [P] [US4] Makefile を作成する（`lint`/`format`/`typecheck`/`test`/`check` の各ターゲットを `uv run` 経由で定義。`format` ターゲットはローカル用でファイルを直接変更する。CI では `ruff format --check .` を使用する旨を Makefile コメントに記述する）`Makefile`

**チェックポイント**: 以下がすべてエラーゼロで完了すること
```
make lint       # ruff check . → 違反ゼロ
make format     # ruff format . → 差分なし
make typecheck  # pyrefly check → エラーゼロ
make test       # pytest → 全テストパス
make check      # 上記 4 つを順に実行
```

---

## Phase 5: ポリッシュ・横断的対応

**目的**: 利用者向けドキュメントの整備と最終確認

- [ ] T010 [P] README.md を作成する（インストール手順・`uv sync`・基本的な使い方・GUI オプション依存 `uv sync --extra gui`・`make` コマンド一覧）`README.md`
- [ ] T011 make check を実行して全 SC を検証する（SC-001〜SC-005 を順に確認し、合否を PR コメントに記録する手動チェックリスト）

---

## 依存関係と実行順序

### フェーズ依存

- **Phase 1（セットアップ）**: 依存なし — 即座に開始可能
- **Phase 2（US1）**: Phase 1 完了後に開始（T001・T002 完了が前提）。T007→T003/T004 の TDD 順序を守ること
- **Phase 3（US2）**: Phase 2 完了後に開始（T003 が `cli.py` に build-annotations を定義済みであること）
- **Phase 4（US4）**: Phase 3 完了後に開始（テストが通る状態でリント設定を追加）
- **Phase 5（ポリッシュ）**: Phase 4 完了後 — T010 は並行開始可能

### ユーザーストーリー依存

- **US1（P1）**: Phase 1 完了後すぐ開始可能。T007（テスト RED）→ T003/T004（実装 GREEN）の TDD サイクルに従う
- **US2（P2）**: US1 完了後（T003 で `cli.py` の骨格が存在すること）— US1 と独立してテスト可能
- **US3（P3）**: US1 の Phase 2 チェックポイントで `uv run pytest` が GREEN になることで達成される（独立フェーズとしては不要）
- **US4（P3）**: US2 完了後（全モジュールが揃いテストが通る状態でリント設定を追加）

### 各ストーリー内の並行機会

- **Phase 1**: T001 と T002 は並行実行可能（異なるファイル）
- **Phase 2（US1）**: T003 と T004 は並行実行可能（`cli.py` と `ui.py`）
- **Phase 3（US2）**: T005 と T006 は並行実行可能（`query.py` と `annotations.py`）
- **Phase 4（US4）**: T008 と T009 は並行実行可能（`pyproject.toml` と `Makefile`）

---

## 並行実行例

### Phase 1

```bash
# Task: T001 — pyproject.toml を作成する
# Task: T002 — nekochan_suggest/__init__.py を作成する  ← 同時実行可能
```

### Phase 2（US1）

```bash
# Task: T007 — tests/test_cli.py を作成する（RED を確認）
# ↓ FAIL を確認したら実装へ
# Task: T003 — cli.py を実装する
# Task: T004 — ui.py を実装する  ← T003 と同時実行可能（異なるファイル）
```

### Phase 3（US2）

```bash
# Task: T005 — query.py を実装する
# Task: T006 — annotations.py を実装する  ← 同時実行可能（異なるファイル）
```

### Phase 4（US4）

```bash
# Task: T008 — pyproject.toml に ruff・pyrefly 設定を追加する
# Task: T009 — Makefile を作成する  ← 同時実行可能（異なるファイル）
```

---

## 実装戦略

### MVP ファースト（US1 のみ）

1. Phase 1（セットアップ）完了
2. Phase 2（US1）完了
3. **停止・検証**: `uv run nekochan-suggest --help` が正常動作することを確認
4. 必要なら US2→US3→US4 へ順に進む

### インクリメンタル・デリバリー

1. Phase 1 + Phase 2（US1）→ コマンドが動作するMVP ✅
2. Phase 3（US2）追加 → パッケージ骨格が完成 ✅
3. Phase 4（US4）追加 → CI 対応のコード品質チェックが整備 ✅
4. Phase 5（ポリッシュ）→ README と最終確認 ✅

---

## メモ

- `[P]` タスクは異なるファイルを対象とし、依存関係がないもの
- `[Story]` ラベルはタスクをユーザーストーリーにトレースするため付与
- 各チェックポイントでストーリーの独立動作を検証してからコミット
- すべての docstring・コードコメントは日本語で記述すること（憲法 原則 V）
- ライブラリコード内での裸の `print()` は使用禁止（`cli.py` の出力のみ例外）
