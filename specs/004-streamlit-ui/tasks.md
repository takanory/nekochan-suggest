# Tasks: nekochan-suggest Streamlit GUI

**Input**: Design documents from `/specs/004-streamlit-ui/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可（別ファイル・未完了タスクへの依存なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2）
- 各タスクに具体的なファイルパスを含む

---

## Phase 1: セットアップ

**目的**: GUI フィーチャーの基盤準備（`pyproject.toml` の確認・`streamlit` インストール）

- [ ] T001 `pyproject.toml` の `[project.optional-dependencies] gui = ["streamlit"]` を確認し `uv sync --extra gui` でインストールする

**チェックポイント**: `streamlit` がインポートできる状態 → Phase 2 へ進める

---

## Phase 2: 基盤（全ユーザーストーリーの前提）

**目的**: `nekochan_suggest/_app.py` の骨格と `ui.py` のエントリーポイントを実装する。
US1・US2 両フェーズが依存するファイル分割構造を確立する。

**⚠️ 重要**: このフェーズが完了するまで US1・US2 の作業を開始しない

- [ ] T002 `tests/test_ui.py` にテストファイルを新規作成し、`suggest()` モック用フィクスチャを定義する（`nekochan_suggest.query.suggest` の `patch` 設定）
- [ ] T003 [P] `nekochan_suggest/_app.py` にモジュール骨格（docstring・型ヒント付き空関数）を新規作成する
- [ ] T004 [P] `nekochan_suggest/ui.py` を更新し `main_run.main([str(_app_path)], standalone_mode=False)` を呼び出す `main()` に書き換える

**チェックポイント**: `_app.py` と `ui.py` が存在し、`pytest tests/test_ui.py` が収集できる状態

---

## Phase 3: US1 — GUI でネコチャン絵文字の提案を受け取る（優先度: P1）🎯 MVP

**ゴール**: テキストを入力して「提案する」ボタンを押すと絵文字名・スコア・画像が縦に表示される

**独立テスト**:
```bash
uv sync --extra gui
nekochan-suggest-ui
# ブラウザで「今日もいい天気ですね」と入力 → 3 件の候補・画像が表示されれば完了
```

**受け入れ基準**:
- 候補 3 件以上表示（絵文字名 + スコア + 画像）
- 空入力時は入力促しメッセージ
- 再入力時は前回結果を上書き

### テスト（US1）

- [ ] T005 [US1] `tests/test_ui.py` に `build_image_url()` 単体テスト追加: `name="yatta-nya"` → 期待 URL を確認する
- [ ] T006 [US1] `tests/test_ui.py` に入力バリデーション単体テスト追加: 空文字列・空白のみ → `suggest()` が呼ばれないことを確認する
- [ ] T007 [US1] `tests/test_ui.py` に 1000 文字超入力テスト追加: 先頭 1000 文字で `suggest()` が呼ばれることを確認する
- [ ] T008 [US1] `tests/test_ui.py` に正常提案フロー統合テスト追加: `suggest(text, count=3)` をモックし 3 件の `SuggestionResult` を返し、`run_suggestion()` が結果リストを返すことを確認する（`count=3` で呼ばれることも検証）

### 実装（US1）

- [ ] T009 [US1] `nekochan_suggest/_app.py` に `build_image_url(name: str) -> str` 関数を実装する（URL パターン: `https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/images/{name}.png`）
- [ ] T010 [US1] `nekochan_suggest/_app.py` に `validate_input(text: str) -> tuple[bool, str]` 関数を実装する（空チェック・1000 文字超トランケート・メッセージ返却）
- [ ] T011 [P] [US1] `nekochan_suggest/_app.py` に `run_suggestion(text: str) -> list[SuggestionResult]` 関数を実装する（`suggest(text, count=3)` を呼び出し、発生した例外はキャッチせずそのまま呼び出し元に raise する）
- [ ] T012 [US1] `nekochan_suggest/_app.py` に Streamlit UI メイン関数 `render_app() -> None` を実装する:
  - `st.title()` でページタイトル設定
  - `st.text_area()` でテキスト入力欄（ラベル: 「提案する文章を入力してください」）
  - `st.button("提案する")` ボタン
  - `validate_input()` によるバリデーション（失敗時 `st.warning()` 表示）
  - `try: run_suggestion()` の結果を表示、`except Exception as e: st.error(f"提案処理でエラーが発生しました: {e}")` でエラー表示（スタックトレース非表示）
  - 結果を縦方向カードで `st.image(url)` + `st.write(name, score)` で表示
  - 0 件時は「候補が見つかりませんでした」を `st.info()` で表示
- [ ] T013 [US1] `nekochan_suggest/_app.py` の `__main__` ガードに `render_app()` 呼び出しを追加し Streamlit 実行エントリーポイントを完成させる

**フォーマットバリデーション**: T005〜T013 がすべて `- [ ] T0XX [US1]` 形式であることを確認

---

## Phase 4: US2 — アノテーション未構築時のエラー案内を受け取る（優先度: P2）

**ゴール**: アノテーションファイルが存在しない場合に `build-annotations` 実行を促すエラーを表示する

**独立テスト**:
```bash
mv ~/.local/share/nekochan-suggest/annotations.json ~/.local/share/nekochan-suggest/annotations.json.bak
nekochan-suggest-ui
# ブラウザにエラーメッセージと build-annotations 案内が表示されれば完了
mv ~/.local/share/nekochan-suggest/annotations.json.bak ~/.local/share/nekochan-suggest/annotations.json
```

**受け入れ基準**:
- アノテーション未存在 → `st.error()` でエラー + `build-annotations` コマンド名を含む案内
- エラー状態で「提案する」押下 → 提案実行せずエラー継続表示

### テスト（US2）

- [ ] T014 [US2] `tests/test_ui.py` にアノテーションファイル非存在テスト追加: `ANNOTATIONS_PATH` が存在しない場合 `render_app()` 内で `suggest()` が呼ばれないことを確認する
- [ ] T015 [P] [US2] `tests/test_ui.py` にエラーメッセージ内容テスト追加: `check_annotations_exist()` が `False` を返す場合に `build-annotations` 文字列を含むメッセージが生成されることを確認する

### 実装（US2）

- [ ] T016 [US2] `nekochan_suggest/_app.py` に `check_annotations_exist() -> bool` 関数を実装する（`ANNOTATIONS_PATH.exists()` を返す）
- [ ] T017 [US2] `nekochan_suggest/_app.py` の `render_app()` 冒頭に `check_annotations_exist()` チェックを追加する: `False` の場合 `st.error()` で「アノテーションファイルが見つかりません。`nekochan-suggest build-annotations` を実行してください。」を表示し `st.stop()` で後続処理を停止する

---

## Phase 5: 仕上げ

**目的**: 品質確認・型チェック・ドキュメント検証

- [ ] T018 [P] `pytest tests/test_ui.py -v --cov=nekochan_suggest/_app.py --cov-report=term-missing` を実行してすべてのテストがパスし、`_app.py` のカバレッジが 80% 以上であることを確認する（憲法 II 準拠）
- [ ] T019 [P] `pyrefly nekochan_suggest/ui.py nekochan_suggest/_app.py` を実行して型エラーがないことを確認する
- [ ] T020 [P] `ruff check nekochan_suggest/ui.py nekochan_suggest/_app.py tests/test_ui.py && ruff format --check nekochan_suggest/ui.py nekochan_suggest/_app.py tests/test_ui.py` を実行してリントエラーがないことを確認する
- [ ] T021 `nekochan_suggest/_app.py` と `ui.py` のすべての公開関数に日本語 docstring が付いていることを確認する（憲法 V 準拠）

---

## 依存グラフ

```
T001（pyproject.toml 確認）
  └─ T002（test_ui.py 骨格）
  └─ T003（_app.py 骨格）
  └─ T004（ui.py 更新）
       └─ T005〜T008（US1 テスト）
       └─ T009〜T013（US1 実装）
            └─ T014〜T015（US2 テスト）  ← T016 の `check_annotations_exist` 実装に依存
            └─ T016〜T017（US2 実装）  ← T012（render_app 初期実装）完了後に追加
                 └─ T018〜T021（仕上げ）
```

US1（Phase 3）と US2（Phase 4）の依存関係:
- US1 は提案フロー全体をカバー（T005〜T013 は自己完結）
- US2 は T012（render_app 初期実装）完了後に `render_app()` を拡張する逐次実装（完全独立ではない）

---

## 並列実行例（US1 フェーズ内）

```bash
# T005〜T008（テスト）を T009〜T012（実装）の前に書く（TDD）
# T009, T010 は異なる関数 → 並列実装可
# T011 は T009 と同じファイルだが別関数 → 並列可（[P] マーク済み）
# T012 は T009〜T011 完了後に実装（3 関数を呼び出すため）
# T013 は T012 完了後に追加
```

---

## 実装戦略

**MVP スコープ（Phase 1 + 2 + 3 のみ）**:
- `T001〜T013` を完了させることで US1（提案フロー）が動作する
- `nekochan-suggest-ui` コマンドが起動し、テキスト入力 → 候補表示の基本フローが完成
- US2（エラー案内）は MVP 後に追加できる独立した機能拡張

**インクリメンタル配信**:
1. T001〜T004（基盤）→ コマンドが起動するだけの状態
2. T005〜T013（US1）→ 提案フルフロー動作
3. T014〜T017（US2）→ アノテーション未存在エラー対応
4. T018〜T021（仕上げ）→ 品質確認

