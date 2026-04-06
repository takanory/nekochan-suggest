# 機能仕様書: テキスト入力によるネコチャン絵文字提案（クエリ機能）

**Feature Branch**: `003-emoji-query`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "ユーザーストーリー1の仕様を作成"  
**Parent Spec**: `001-nekochan-suggest` / ユーザーストーリー 1

## ユーザーシナリオとテスト（必須）

### ユーザーストーリー 1 — 文章に合うネコチャン絵文字のファイル名を提案してもらう（優先度: P1）

ユーザーが文章をコマンドラインに入力すると、ツールがローカルの絵文字データ
（事前に `build-annotations` で生成済み）の中からその文章に最も意味・感情的に
近い絵文字のファイル名を複数返す。ユーザーはそのファイル名を Sphinx ドキュメント
や他のツールで使用する。

**この優先度の理由**: このツールの存在価値そのものであり、これ単体で価値ある
MVP となる。

**独立テスト**: `nekochan-suggest "今日もいい天気ですね"` を実行し、
`hare-nya` や `niko-nya` 等の画像ファイル名候補リストが標準出力に表示されれば
完結する（アノテーションファイルは事前に用意する）。

**受け入れシナリオ**:

1. **Given** ポジティブな文章（例：「今日のランチ最高だった！」）と事前生成済みのアノテーションファイル、
   **When** `nekochan-suggest "今日のランチ最高だった！"` を実行する、
   **Then** 候補が 3 件、各候補に画像ファイル名（例: `yatta-nya`）と
   類似度スコア（例: `0.87`）が付いて標準出力に表示される。

2. **Given** ネガティブなトーンの文章（例：「あーもう疲れた…」）と事前生成済みのアノテーションファイル、
   **When** コマンドに渡す、
   **Then** トーンに合ったファイル名（例: `kyukei-nya`, `nemui-nya`）が候補に含まれる。

3. **Given** `echo "眠い" | nekochan-suggest` のように標準入力から文章を渡す、
   **When** 実行する、
   **Then** コマンドライン引数渡しと同様の形式で結果が返る。

4. **Given** `--count 5 "おはよう"` と指定する、
   **When** 実行する、
   **Then** 候補が正確に 5 件返る。

5. **Given** `--json "おはよう"` と指定する、
   **When** 実行する、
   **Then** `{"suggestions": [{"name": "...", "score": 0.8734567}]}` 形式の
   有効な JSON が標準出力に出力される。

---

### エッジケース

- 空文字列を渡した場合、エラーメッセージを stderr に出力して終了コード 1 で終了する。
- 空白のみの文章（例: `"   "`・`"\t\n"`）を渡した場合、strip 後に空文字列として扱い、
  `Error: text is empty.` を stderr に出力して終了コード 1 で終了する（入力は sentence-transformers に送らない）。
- 1000 文字超の文章を渡した場合、文字数制限エラーを stderr に出力して終了コード 1 で終了する。
- `--count 0` や負数を渡した場合、バリデーションエラーを stderr に出力して終了コード 1 で終了する。
- `--count` を省略した場合、デフォルト 3 件を返す。
- アノテーションファイルが存在しない場合、`build-annotations` の実行を促すメッセージを
  stderr に出力して終了コード 1 で終了する。
- モデルのロードやエンコードに失敗した場合、エラーメッセージを stderr に出力して終了コード 1 で終了する。
- 埋め込み結果が空または不正な形状（次元数が 0 等）の場合、
  エラーとして捕捉し、原因ヒント付きメッセージを stderr に出力して終了コード 1 で終了する。
- 日本語以外の文章（英語等）を渡した場合も正常に動作する。
- アノテーションファイル内の `embedding` フィールドが欠損しているレコードはスキップする。
- コマンドライン引数と stdin の両方が指定された場合（例: `echo "眠い" | nekochan-suggest "おはよう"`）、コマンドライン引数を優先し stdin は無視する。

---

## 要件（必須）

### 機能要件

- **FR-001**: ツールはテキスト入力（コマンドライン引数または標準入力）を受け取り、
  ネコチャン絵文字の画像ファイル名の候補と類似度スコアを返さなければならない。
- **FR-002**: 各候補は、画像ファイル名（例: `yatta-nya`）と
  コサイン類似度スコア（0〜1 の浮動小数点）を含まなければならない。
- **FR-003**: デフォルトで 3 件の候補を返さなければならない。
- **FR-004**: `--count N` オプションで候補数を 1〜10 の範囲で指定できなければならない。
  範囲外の値（0 以下または 11 以上）を指定した場合はバリデーションエラーとし、
  `Error: --count out of range (1-10).` を stderr に出力して終了コード 1 で終了する。
  N がアノテーションファイルの実際のエントリ数を超える場合は、利用可能な件数をすべて返す（エラーなし・警告なし）。
- **FR-005**: `--json` フラグを指定すると、結果を JSON 形式で標準出力に出力しなければならない
  （`{"suggestions": [{"name": "...", "score": 0.8734567}]}`）。
  JSON 出力の `score` 値は丸めなしの生の浮動小数点とする。
  `--json` なしのテキスト出力は `N. <ファイル名>  <スコア>` 形式とする
  （例: `1. yatta-nya  0.87`。スコアは小数点以下 2 桁固定）。
- **FR-006**: エラー（空入力・バリデーション違反・アノテーション未生成・モデルロード失敗等）は
  stderr に出力し、終了コード 1 で終了しなければならない。
  エラーメッセージはすべて英語で出力する（例: `Error: annotations file not found. Run 'nekochan-suggest build-annotations' first.`）。
- **FR-007**: クエリ処理には、事前生成済みのアノテーションファイル
  （`~/.local/share/nekochan-suggest/annotations.json`）を使用しなければならない。
  ファイルの読み込みには Python 標準ライブラリの `json` モジュールを使用する。
  ファイルのトップレベル構造は配列（`[{...}, ...]`）とする。
- **FR-008**: 標準入力からのパイプ入力（`echo "文章" | nekochan-suggest`）をサポートしなければならない。
  コマンドライン引数と stdin が両方指定された場合はコマンドライン引数を優先し、stdin は無視する。
- **FR-010**: クエリ時のマッチングには埋め込みベクトルによるコサイン類似度検索を使用しなければならない。
  入力文章を埋め込みベクトルに変換し、アノテーションファイルに保存済みのベクトルと比較して
  上位 N 件を返す。
- **FR-011**: アノテーションファイルが存在しない場合、`build-annotations` の実行を促す
  エラーメッセージを stderr に出力しなければならない。
- **FR-012**: 埋め込み生成には `sentence-transformers` PyPI パッケージを使用しなければならない。
  デフォルト埋め込みモデルは `intfloat/multilingual-e5-base`（768 次元）。
  埋め込み生成時には非対称検索（asymmetric search）のプレフィックス規約に従う:
  - クエリテキストのエンコード: `"query: " + text`
  - アノテーションのエンコード（build-annotations 側）: `"passage: " + annotation`
  コサイン類似度の計算は Python 標準ライブラリ（`math` モジュール）のみで実装し、
  numpy 等の追加 PyPI 依存をコサイン計算に使用してはならない。378 件程度のエントリ数であれば
  純 Python 実装でも SC-001（1 秒以内）を達成できる。
  モデルが未ダウンロードの場合（初回実行時）、`Downloading model <model_name>...` を
  stderr に 1 行出力する。sentence-transformers のデフォルト進捗ログは抑制しない（介入なし）。
  **補足**: sentence-transformers 側の進捗出力（tqdm 等）は CLI 層で制御しないため、
  初回ダウンロード時は sentence-transformers が出力するログとともに上記メッセージが表示される場合がある。
- **FR-013**: 設定ファイル（`~/.config/nekochan-suggest/config.toml`、TOML 形式）または
  以下の環境変数でモデルを変更できなければならない。設定ファイルの読み込みには Python 標準ライブラリの `tomllib` を使用する。
  設定ファイルが存在しない場合はデフォルト値を使用する。
  TOML キーはフラット構造とし、以下のキーを使用する:
  - `embed_model`: 埋め込みモデル名（デフォルト: `intfloat/multilingual-e5-base`）
  - `llm_model`: LLM モデル名（デフォルト: `qwen3.5`）
  環境変数の各名称と対応する config.toml キーは以下の通り:
  - `NEKOCHAN_EMBED_MODEL` → `embed_model`
  - `NEKOCHAN_LLM_MODEL` → `llm_model`
  環境変数は設定ファイル値より優先される。

### キーエンティティ

- **NekochanEmoji（アノテーションファイル内の 1 レコード）**:
  - ファイル全体のトップレベル構造: 配列（`[{...}, ...]`）
  - `name`: 画像ファイル名（例: `yatta-nya`）
  - `annotation`: LLM が生成した英語の説明テキスト
  - `embedding`: annotation から生成した埋め込みベクトル（浮動小数点の配列）
- **SuggestionResult（提案結果の 1 件）**:
  - Python 実装: `dataclass`（`result.name`・`result.score` でアクセス）
  - `name`: 画像ファイル名
  - `score`: コサイン類似度スコア（0〜1 の浮動小数点、小数点以下 2 桁で表示）
- **QueryInput（入力パラメータの概念的記述 — コード上の型としては実装しない）**:
  - `text`: 提案を求める文章（1 文字以上・1000 文字以下）
  - `count`: 候補数（1〜10、デフォルト 3）
  - `json_mode`: 標準出力のフォーマットを CLI 層で切り替えるフラグ（`suggest()` には渡さず CLI 層で処理）

---

## 成功基準（必須）

### 測定可能な成果

- **SC-001**: LLM の埋め込み生成を除いたツール自体の処理（入力解析・類似度計算・出力整形）が
  1 秒以内に完了する。
- **SC-002**: 入力文章の意味・トーンに合ったファイル名が、提案候補の中に
  80% 以上の確率で含まれる（5 件の異なるトーンの文章でテストした場合）。
  検証方法: 5 文の検証用クエリと期待ファイル名をチェックリストで定義し、
  手動検証（CI 外）で実施する（LLM ・埋め込みモデルの品質に依存する非決定論的指標のため自動化は行わない）。
- **SC-003**: `--json` 出力が常に有効な JSON として解析できる。
- **SC-004**: エラー発生時に、ユーザーが原因と対処法を理解できるメッセージが
  stderr に表示され、終了コード 1 で終了する。
- **SC-005**: `--count` の範囲（1〜10）内であれば、指定した件数と同数の候補を常に返す
  （アノテーションファイルに十分な件数が存在する場合）。

---

## 前提と想定

- アノテーションファイル（`~/.local/share/nekochan-suggest/annotations.json`）は
  別フィーチャー（build-annotations サブコマンド）で事前生成されている。
  本フィーチャーはアノテーションファイルの生成を行わない。
- `sentence-transformers` はローカルに pip インストール済みであること（本パッケージの依存として自動インストール）。
- デフォルト埋め込みモデルは `intfloat/multilingual-e5-base`（初回実行時に Hugging Face から自動ダウンロード）。
- 本フィーチャーで追加するプロダクション PyPI 依存は `sentence-transformers` のみ（開発依存の `pytest-cov` は除く）。それ以外の処理には Python 標準ライブラリのみを使用する。
- 設定ファイルが存在しない場合、すべてデフォルト値を使用して正常動作する。
- アノテーションはすべて英語で保存されているため、日本語・英語の両方のクエリに対応できる。
- `intfloat/multilingual-e5-base` モデルの非対称検索仙5様: クエリテキストには `"query: "` プレフィックス、アノテーション埋め込み（build-annotations 側）には `"passage: "` プレフィックスを付与する。
  この検索時に `_embed_text()` 内で `"query: " + text` としてエンコードする。
- アノテーションファイルの `embedding` フィールドが欠損しているレコードはスキップする。
- 本フィーチャーは `query.py` モジュールにビジネスロジックを実装し、`cli.py` からは
  ライブラリ関数として呼び出す形で設計する（GUI 連携を考慮）。
- 単体テストは `tests/fixtures/` に配置した小規模ダミー annotations.json フィクスチャと
  `unittest.mock` を用いた `sentence-transformers` パッケージ呼び出しのモックで実施する。CI 上でモデルダウンロード不要とし、
  コサイン類似度計算等の純 Python ロジックを決定論的にテストできる。
- `query.py` の公開 API は `suggest(text, count) -> list[SuggestionResult]` の 1 関数に集約する。
  内部機能（`_load_annotations`・`_embed_text`・`_cosine_similarity`）はモジュール内部関数として分離し、許可なく公開 API としない。

## 明確化セッション

### セッション 2026-03-22 (4)

- Q: 埋め込み生成に `sentence-transformers` PyPI パッケージを使用するか → A: `sentence-transformers` PyPI パッケージを追加して使用する（コサイン類似度計算は引き続き純 Python）- Q: デフォルト LLM モデル → A: `qwen3.5`（`qwen2.5` から変更）
- Q: `annotations.json` のトップレベル JSON 構造 → A: 配列（`[{"name": "yatta-nya", "annotation": "...", "embedding": [...]}]`）
- Q: `--json` 出力の `score` 値のフォーマット → A: 生の浮動小数点（丸めなし、例: `0.8734567`）
- Q: LLM モデル名の環境変数名 → A: `NEKOCHAN_LLM_MODEL`（config.toml の `llm_model` キーと対称）
- Q: `QueryInput` をコード型として実装するか → A: 概念的ドキュメントのみ（`suggest()` は個別引数 `text, count` で呼び出す、`json_mode` は CLI 層が処理）
- Q: 空白のみ文章（`"   "` 等）を渡した場合の挙動 → A: strip 後に空なら `Error: text is empty.` を stderr に出力して終了コード 1

- Q: 単体テストでモデルダウンロードに依存しない検証方法 → A: `tests/fixtures/` にダミー annotations.json を配置し `unittest.mock` で `sentence-transformers` パッケージ呼び出しをモック（CI でモデルダウンロード不要）
- Q: `query.py` の公開 API の粒度 → A: `suggest(text, count) -> list[SuggestionResult]` の 1 関数に集約し、内部機能は非公開
- Q: エラーメッセージの言語 → A: 英語（例: `Error: annotations file not found.`）
- Q: `SuggestionResult` の Python 型表現 → A: `dataclass`（`result.name`・`result.score` でアクセス）

- Q: コサイン類似度の計算に numpy を追加するか、純 Python（stdlib のみ）で実装するか → A: 純 Python（math モジュール使用、追加依存なし）
- Q: `--count N` がアノテーションファイルの実際エントリ数を超えた場合の挙動 → A: 利用可能な件数をすべて返す（エラーなし・警告なし）
- Q: 設定ファイル（config.toml）の TOML キー名の構造 → A: フラット構造（`embed_model`、`llm_model`）
- Q: SC-002（80%以上の提案精度）の検証方法 → A: 手動検証（5文のクエリと期待ファイル名をチェックリスト定義、CI 外で実施）
- Q: sentence-transformers のエンコードが不正な結果を返した場合の挙動 → A: 例外として捕捉し、原因ヒント付きメッセージを stderr に出力して終了コード 1

### セッション 2026-04-04

- Q: `intfloat/multilingual-e5-base` モデルのエンコードプレフィックスの扱い—検索クエリとアノテーション（build-annotations）で同じプレフィックスを使うか → A: 非対称検索を採用。クエリ側は `"query: "` プレフィックス、アノテーション側（build-annotations）は `"passage: "` プレフィックスを付与する（e5 モデル公式推奨仕様）
- Q: `--timeout` オプションを削除するか → A: 削除する（`sentence-transformers` はローカル処理のためタイムアウト不要）
- Q: コマンドライン引数と stdin が同時指定された場合の優先順位 → A: コマンドライン引数を優先し stdin を無視する
- Q: モデル未ダウンロード時（初回実行）の CLI 通知方法 → A: stderr に `Downloading model <model_name>...` を 1 行出力する（sentence-transformers のデフォルト進捗ログはそのまま表示）
- Q: `--count` 範囲外エラーのメッセージ文言 → A: `Error: --count out of range (1-10).`