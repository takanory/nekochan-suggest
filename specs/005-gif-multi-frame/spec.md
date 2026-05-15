# Feature Specification: GIF Multi-Frame Annotation Generation

**Feature Branch**: `005-gif-multi-frame`  
**Created**: 2026-05-07  
**Status**: Draft  
**Input**: User description: "動画GIFの場合にはPillowを使用して複数フレームの画像を取得し、一連の画像としてLLMに渡してannotationを生成する"

## User Scenarios & Testing *(mandatory)*


  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Animated GIF produces richer annotation (Priority: P1)

`build-annotations` 実行時、アニメーション GIF 絵文字を Pillow で複数フレームに
分解し、全フレームを画像シーケンスとして LLM に渡すことでアノテーションを生成する。
単一フレームのアプローチと比べ、絵文字のアニメーション的な文脈を反映したより
豊かなアノテーションが得られる。

**Why this priority**: ねこちゃん絵文字セットのうちアニメーション GIF が相当数を占める。
1フレームのみ渡す方式では絵文字の動きや意味が失われる。これがこのフィーチャーの
中心的な価値であり最優先事項。

**Independent Test**:
```bash
nekochan-suggest build-annotations --dry-run
# → GIF 絵文字のアノテーションにアニメーション的な語句が含まれることを確認
```

**Acceptance Scenarios**:

1. **Given** `nekochan_emoji.json` にアニメーション GIF 絵文字が存在する、**When** `build-annotations` が実行される、**Then** GIF から複数フレームが抽出され、すべてのフレームが LLM リクエストの images フィールドにリストとして含まれる。
2. **Given** N フレームの GIF、**When** フレームが抽出される、**Then** 設定された最大フレーム数以下のフレームが使用される。
3. **Given** 1フレームのみの GIF、**When** 処理される、**Then** そのフレームが単一画像として渡される（PNG と同じ挙動）。
4. **Given** PNG または JPEG 画像、**When** 処理される、**Then** 挙動は変わらず単一画像として渡される。

---

### User Story 2 - Frame count is configurable (Priority: P2)

LLM に渡す GIF フレームの最大数を環境変数で設定可能にする。アノテーション品質と
処理時間・トークン使用量のバランスを調整できる。

**Why this priority**: デプロイ環境によってトークン制限や速度要件が異なる。
ハードコードされた上限では柔軟性が失われる。

**Independent Test**:
```bash
NEKOCHAN_GIF_MAX_FRAMES=2 nekochan-suggest build-annotations --dry-run
```

**Acceptance Scenarios**:

1. **Given** `NEKOCHAN_GIF_MAX_FRAMES=N` が設定されている、**When** GIF の `build-annotations` が実行される、**Then** 最大 N フレームが抽出されて LLM に渡される。
2. **Given** 環境変数が未設定、**When** GIF を処理する、**Then** デフォルトのフレーム上限（4フレーム）が使用される。

---

### Edge Cases

- GIF が1フレームのみの場合 → 単一画像として扱う（PNG と同じ挙動）。
- GIF が壊れていて Pillow が読めない場合 → 既存のエラーハンドリングでスキップ・警告。
- `NEKOCHAN_GIF_MAX_FRAMES=0` または負の値の場合 → デフォルト（4）を使用。
- GIF のフレーム数が最大値より少ない場合 → 全フレームを使用。
- Ollama が複数画像リクエストに失敗した場合 → 既存のエラーハンドリングでスキップ・警告。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `build-annotations` は Pillow を使用してアニメーション GIF から複数フレームを抽出しなければならない。
- **FR-002**: 抽出されたすべてのフレームは、単一の LLM リクエストで images シーケンスとして渡されなければならない。
- **FR-003**: 各フレームは LLM に渡す前に PNG 形式に変換されなければならない（Ollama は PNG/JPEG のみサポート）。
- **FR-004**: GIF ごとに抽出するフレームの最大数は `NEKOCHAN_GIF_MAX_FRAMES` 環境変数で設定可能でなければならない。
- **FR-005**: デフォルトの最大フレーム数は 4 でなければならない。
- **FR-006**: GIF のフレーム数が最大値より少ない場合は全フレームを使用しなければならない。
- **FR-007**: GIF のフレーム数が最大値を超える場合、均等間隔でフレームをサンプリングしなければならない。インデックスは `i * (total - 1) // (N - 1)` (i = 0, 1, ..., N-1) で算出し、最初と最後のフレームを必ず含む。N=1 の特殊ケースではインデックス 0 のみを使用する。
- **FR-008**: PNG/JPEG などの非 GIF 画像は変更なく単一画像として処理されなければならない。
- **FR-009**: `annotations.json` に保存する `image_base64` と `image_mimetype` は元の GIF データのまま保持されなければならない（変換後フレームは保存しない）。
- **FR-010**: フレーム抽出エラーは既存のスキップ機構（ログ記録・警告）で処理されなければならない。
- **FR-011**: GIF を複数フレームで処理する場合、LLM へのプロンプト先頭にアニメーションである旨とフレーム数を追記しなければならない（例: "These are N frames from an animated GIF emoji. "）。
- **FR-012**: `build-annotations` 実行時、GIF を含むすべての既存アノテーションエントリはスキップされなければならない。再生成が必要な場合はアノテーションファイルから該当エントリを削除してから実行すること。

### Key Entities

- **GifFrames**: 1つのアニメーション GIF から抽出した PNG base64 画像のシーケンス。LLM の `images` フィールドにリストとして渡す。永続化しない。
- **AnnotationRecord**: 変更なし。`image_base64` は元の GIF データ、`image_mimetype` は `"image/gif"` を保持する。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: nekochan 絵文字セット内の全 GIF 絵文字がエラーなく処理される（GIF 関連のスキップがエラーレポートに現れない）。
- **SC-002**: アニメーション GIF 絵文字のアノテーションにアニメーション的な文脈が反映されている — データセットからサンプリングした 5 件の GIF 絵文字を手動確認して検証。
- **SC-003**: GIF 絵文字1件あたりの処理時間が同等ファイルサイズの PNG 絵文字の 3 倍を超えない（自動計測は困難なため、手動の定性的確認とする）。
- **SC-004**: フレーム抽出関数はユニットテストで 100% カバレッジを達成する。

### Non-Functional Requirements

- **NF-001**: GIF フレーム抽出時、抽出フレーム数を DEBUG レベルでログ出力しなければならない（例: `"Extracted 4 frames from gif: cat_wave.gif"`）。

## Clarifications

### Session 2026-05-08

- Q: GIF フレームのサンプリング方法（フレーム数が最大値を超える場合） → A: 均等間隔（先頭・末尾を含む）: インデックス `i * (total-1) // (N-1)` (i=0..N-1)
- Q: マルチフレーム処理時にプロンプトへアニメーション旨を追記するか → A: 追記する（"These are N frames from an animated GIF emoji."）
- Q: 既存の GIF アノテーション（1フレーム方式で生成済み）を再生成するか → A: 再生成する（既存エントリを上書き）
- Q: Pillow を `pyproject.toml` のどこに追加するか → A: core dependencies
- Q: GIF 処理時に抽出フレーム数をログ出力するか → A: DEBUG レベルで出力する（例: "Extracted 4 frames from gif: cat_wave.gif"）

## Assumptions

- Ollama（gemma4:e4b）は `api/generate` リクエストの `images` 配列で複数画像を受け付ける。
- Pillow は `005-gif-support` ブランチで導入済みであり環境に存在する。`pyproject.toml` の `[project.dependencies]`（core）に追加する。
- デフォルト4フレームは、トークン予算を超えずに典型的なねこちゃん GIF のアニメーション意図を捉えるのに十分である。
- フレームは均等間隔でサンプリングする（先頭 N フレームではなく）。

