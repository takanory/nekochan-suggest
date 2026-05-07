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
- **FR-007**: GIF のフレーム数が最大値を超える場合、均等間隔でフレームをサンプリングしなければならない。
- **FR-008**: PNG/JPEG などの非 GIF 画像は変更なく単一画像として処理されなければならない。
- **FR-009**: `annotations.json` に保存する `image_base64` と `image_mimetype` は元の GIF データのまま保持されなければならない（変換後フレームは保存しない）。
- **FR-010**: フレーム抽出エラーは既存のスキップ機構（ログ記録・警告）で処理されなければならない。

### Key Entities

- **GifFrames**: 1つのアニメーション GIF から抽出した PNG base64 画像のシーケンス。LLM の `images` フィールドにリストとして渡す。永続化しない。
- **AnnotationRecord**: 変更なし。`image_base64` は元の GIF データ、`image_mimetype` は `"image/gif"` を保持する。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: nekochan 絵文字セット内の全 GIF 絵文字がエラーなく処理される（GIF 関連のスキップがエラーレポートに現れない）。
- **SC-002**: アニメーション GIF 絵文字のアノテーションにアニメーション的な文脈が反映されている — データセットからサンプリングした 5 件の GIF 絵文字を手動確認して検証。
- **SC-003**: GIF 絵文字1件あたりの処理時間が同等ファイルサイズの PNG 絵文字の 3 倍を超えない。
- **SC-004**: フレーム抽出関数はユニットテストで 100% カバレッジを達成する。

## Assumptions

- Ollama（gemma4:e4b）は `api/generate` リクエストの `images` 配列で複数画像を受け付ける。
- Pillow は `005-gif-support` ブランチで導入済みであり環境に存在する。
- デフォルト4フレームは、トークン予算を超えずに典型的なねこちゃん GIF のアニメーション意図を捉えるのに十分である。
- フレームは均等間隔でサンプリングする（先頭 N フレームではなく）。

