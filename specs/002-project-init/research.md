# Phase 0 リサーチ: プロジェクト初期化

**作成日**: 2026-03-20  
**フィーチャー**: `002-project-init`

## 調査項目と結論

---

### 1. uv による Python パッケージ初期化と optional dependency group

**Decision**: `uv init --package` でパッケージ型プロジェクトを初期化後、
`pyproject.toml` を手動で調整する形を採用する。

**Rationale**:
- `uv init --package` は `pyproject.toml`（PEP 621）と `src/` レイアウトを生成するが、
  本プロジェクトはフラット構成のため `src/` レイアウトは不要。
- GUI オプション依存は `[project.optional-dependencies]` の `gui` グループで定義する:
  ```toml
  [project.optional-dependencies]
  gui = ["streamlit"]
  ```
  インストールは `uv sync --extra gui` で行う。
- 開発依存は `[tool.uv.dev-dependencies]` または `[dependency-groups]` に記述:
  ```toml
  [dependency-groups]
  dev = ["pytest>=8.0", "ruff>=0.9", "pyrefly>=0.19"]
  ```
- `uv sync` で dev 依存まで一括インストール、`uv run nekochan-suggest` で仮想環境内実行。

**Alternatives considered**: `pip` + `setup.py` → `uv` の方が高速・設定が一元化されるため却下。

---

### 2. pyrefly の pyproject.toml 設定フォーマット

**Decision**: `[tool.pyrefly]` セクションを `pyproject.toml` に直接記述する。

**Rationale**:
- `pyrefly init pyproject.toml` を実行すると `[tool.pyrefly]` を自動生成することを確認。
- 生成される基本形:
  ```toml
  [tool.pyrefly]
  project-includes = [
      "nekochan_suggest/**/*.py",
      "tests/**/*.py",
  ]
  ```
- `project-includes` でチェック対象ディレクトリを明示することで、
  `uv run pyrefly check` が正しいファイルを対象にする。
- 独立した `pyrefly.toml` を作らず `pyproject.toml` に集約することで設定ファイルを最小化。

**Alternatives considered**: 専用 `pyrefly.toml` → 設定ファイルが分散するため却下。

---

### 3. ruff の pyproject.toml 設定フォーマット

**Decision**: `[tool.ruff]` と `[tool.ruff.lint]` セクションを `pyproject.toml` に記述する。

**Rationale**:
- ルールセット `["E", "F", "I", "N", "UP"]` に対応する設定:
  ```toml
  [tool.ruff]
  target-version = "py311"
  line-length = 88

  [tool.ruff.lint]
  select = ["E", "F", "I", "N", "UP"]
  ```
  - `E`: pycodestyle エラー（構文・スタイル違反）
  - `F`: Pyflakes（未使用インポート・未定義変数）
  - `I`: isort（import 順序）
  - `N`: pep8-naming（命名規則）
  - `UP`: pyupgrade（Python バージョンアップグレード提案）
- `ruff check .` でリント、`ruff format .` でフォーマット（black 互換）。
- `--check` フラグを使うことで CI でのドライラン確認が可能。

**Alternatives considered**: `["ALL"]` からの除外方式 → 初期段階では管理が重い、警告ゼロを保ちにくいため却下。

---

### 4. Makefile によるタスクランナー

**Decision**: `Makefile` をプロジェクトルートに配置し、すべての開発タスクを `make <target>` で統一する。

**Rationale**:
- `make` は GitHub Actions の `ubuntu-latest` / `macos-latest` ランナーに標準搭載。追加インストール不要。
- `uv run` 経由で呼び出すことで仮想環境の有効化を不要にできる:
  ```makefile
  .PHONY: lint format typecheck test check

  lint:
  	uv run ruff check .

  format:
  	uv run ruff format .

  typecheck:
  	uv run pyrefly check

  test:
  	uv run pytest

  check: lint typecheck test
  ```
- `make check` で lint → typecheck → test を順に実行。CI では `make check` を 1 行で記述できる。
- `format` は CI では `ruff format --check .`（差分検出のみ）に切り替えることを推奨するが、
  Makefile 内でのフラグ変数化（`make format CHECK=--check`）も可能。

**Alternatives considered**:
- `tox` → 複数 Python バージョンのマトリックステスト不要のため過剰。
- `just` → 追加インストールが必要（CI ランナーに非標準）。
- `uv run` エイリアス → `pyproject.toml` の `uv.scripts` 機能はバージョン依存性があり安定性が低い。

---

### 5. エントリーポイントの定義方法

**Decision**: `[project.scripts]` で両コマンドを定義する。

**Rationale**:
```toml
[project.scripts]
nekochan-suggest = "nekochan_suggest.cli:main"
nekochan-suggest-ui = "nekochan_suggest.ui:main"
```
- `uv sync` 後に `nekochan-suggest` コマンドが仮想環境の `bin/` に生成される。
- `uv run nekochan-suggest` または `uv run --no-dev nekochan-suggest` で実行可能。
- スタブ実装: `cli.py::main()` と `ui.py::main()` は `print("未実装 (別フィーチャーで実装予定)")` を返す。

---

## 未解決事項

なし。すべての NEEDS CLARIFICATION は解消済み。
