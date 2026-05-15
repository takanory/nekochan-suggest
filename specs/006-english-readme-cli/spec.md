# Feature Specification: English README and CLI Localization

**Feature Branch**: `006-english-readme-cli`  
**Created**: 2026-05-15  
**Status**: Draft  
**Input**: User description: "READMEとコマンドラインを英語にする。READMEは日本語は別ファイルにしてREADME.mdからリンクする"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - English README with Japanese link (Priority: P1)

An English-speaking developer discovers `nekochan-suggest` on GitHub or PyPI.
They read `README.md` in English, understand what the tool does, how to install
it, and how to use the CLI — without needing to know Japanese.
A clearly visible link in `README.md` points to a Japanese version
(`README.ja.md`) for Japanese-speaking users.

**Why this priority**: The primary distribution channel (GitHub, PyPI) is
international. An English README is the standard expectation for open-source
projects and is essential for discoverability.

**Independent Test**: Open `README.md` — all prose, section headings, CLI
examples, and captions are in English. A link to `README.ja.md` is present near
the top. `README.ja.md` exists and contains the full Japanese content.

**Acceptance Scenarios**:

1. **Given** the repository root, **When** a user reads `README.md`,
   **Then** all content is in English and a link to `README.ja.md` appears
   within the first 10 lines.
2. **Given** the repository root, **When** a user opens `README.ja.md`,
   **Then** the full Japanese documentation is present.
3. **Given** `README.md`, **When** a developer looks for installation
   instructions, **Then** they find English commands and descriptions.

---

### User Story 2 - English CLI help and output (Priority: P2)

A developer runs `nekochan-suggest --help` or
`nekochan-suggest build-annotations --help` and reads all help text, error
messages, and progress output in English.

**Why this priority**: Internationalizing CLI output makes the tool usable in
non-Japanese terminals and allows integration in CI pipelines with English log
parsers.

**Independent Test**: Run `nekochan-suggest --help` and
`nekochan-suggest build-annotations --help`; all displayed text is in English.
Run the tool and observe that progress/error messages are in English.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** a user runs `nekochan-suggest --help`,
   **Then** all help text is in English.
2. **Given** the CLI is installed, **When** `build-annotations` encounters an
   error (e.g., Ollama not running), **Then** the error message printed to stderr
   is in English.
3. **Given** `build-annotations` is running, **When** progress is printed to
   stderr, **Then** status messages are in English (e.g., skip/error notices).

---

### Edge Cases

- A user who previously bookmarked the Japanese README URL — the Japanese content
  must remain accessible at `README.ja.md`.
- Internal `logging` debug/info messages (not shown to end users by default)
  are out of scope and may remain in Japanese.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `README.md` MUST be written entirely in English.
- **FR-002**: `README.md` MUST contain a link to `README.ja.md` within the first
  10 lines of the file (e.g., immediately after the title).
- **FR-003**: `README.ja.md` MUST exist and contain up-to-date Japanese
  documentation reflecting the current implementation state (not a verbatim
  copy of the old stale README).
- **FR-004**: All CLI `argparse` help strings, description strings, AND
  runtime user-facing messages printed to stdout/stderr (e.g., error notices,
  skip notices, progress status lines) MUST be in English.
- **FR-005**: The `pyproject.toml` `description` field MUST be updated to
  English. Other fields and comments are out of scope.

### Assumptions

- Internal Python `logging` module messages (DEBUG/INFO, not visible to users
  by default) are out of scope and may remain in Japanese.
- The Streamlit UI (`nekochan-suggest-ui`) is out of scope; only the CLI and
  README files are covered by this feature.
- Both README files MUST cover the same sections (installation, usage, development,
  license) with equivalent information.
- No new tests are added for this feature; existing test assertions that reference
  Japanese strings MUST be updated to match the new English messages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `README.md` contains zero Japanese characters.
- **SC-002**: `README.ja.md` exists and contains all sections present in the
  current Japanese `README.md`.
- **SC-003**: Running `nekochan-suggest --help` and
  `nekochan-suggest build-annotations --help` produces output containing zero
  Japanese characters.
- **SC-004**: `README.md` contains a visible hyperlink to `README.ja.md` within
  the first 10 lines of the file.
- **SC-005**: `uv run pytest tests/` passes with all existing tests updated to
  match the new English CLI messages.

## Clarifications

### Session 2026-05-15

- Q: CLI 英語化のスコープは `--help` テキストのみか、実行時メッセージも含むか？ → A: `--help` テキスト＋実行時ユーザー向けメッセージ（`print` / `stderr`）をすべて英語化
- Q: `README.ja.md` の内容は現行 README をそのまま移動するか、最新実装を反映して更新するか？ → A: 最新の実装状態を反映した内容で新規作成する
- Q: `pyproject.toml` の英語化スコープ？ → A: `description` フィールドのみ。その他のフィールド・コメントは対象外
- Q: CLI 英語化に対するテストの対応？ → A: 新規テストは追加せず、既存テストのアサーション文字列を英語に更新するのみ
