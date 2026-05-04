# リサーチ結果: ネコチャン絵文字アノテーション構築コマンド（build-annotations）

**フィーチャー**: `001-nekochan-suggest`  
**ブランチ**: `001-nekochan-suggest`  
**日付**: 2026-05-04

---

## 1. Ollama API — マルチモーダル画像送信

**決定**: `POST /api/generate` に `{"model": "qwen3.5:2b", "prompt": "...", "stream": false, "images": ["<base64>"]}` を送信する

**根拠**:
- Ollama の `images` フィールドはマルチモーダルモデルで有効（base64 文字列の配列）
- `urllib.request.urlopen` で直接 HTTP 呼び出し（追加ライブラリ不要）
- `stream: false` にすることで単一 JSON レスポンスを同期受信できる

**検討した代替案**:
- `ollama` PyPI パッケージ: 憲法 I（標準ライブラリ優先）に違反するため却下
- Ollama Embeddings API: テキスト埋め込みには `sentence-transformers` を使用するため不要

---

## 2. GIF 画像のスキップ方針

**決定**: `mimetype == "image/gif"` の絵文字はアノテーション生成・埋め込み生成・保存をスキップし、完了後に `skipped_gif` リストを stderr に報告する

**根拠**:
- `qwen3.5:2b` は GIF アニメーション画像を処理できない（マルチモーダル非対応形式）
- アノテーションのない絵文字をクエリ候補にすると品質が保証できない
- GIF スキップは一時的な制限であり、将来 GIF 対応モデルへの切り替えで再考可能（spec.md 明確化セッション参照）
- LLM エラーのスキップと分けて報告することでユーザーが原因を識別できる

**検討した代替案**:
- GIF を画像なしでアノテーション生成: 実装済みだったが GIF 専用の記述精度が低下するため却下
- GIF のアノテーション結果を空文字列で保存: 候補品質を損なうため却下

---

## 3. 埋め込みモデルとプレフィックス設計

**決定**: `sentence-transformers`（`intfloat/multilingual-e5-base`）を使用し、アノテーション側に `"passage: "` プレフィックスを付与する（クエリ側は `"query: "` プレフィックス）

**根拠**:
- `003-emoji-query` フィーチャーと統一（既存実装との互換性）
- `multilingual-e5-base` は日英両言語に対応し、日本語クエリ → 英語アノテーションの非対称検索が可能
- 非対称検索では passage/query プレフィックスがコサイン類似度の精度向上に寄与する

**検討した代替案**:
- Ollama Embeddings API: 憲法 I + `003-emoji-query` との統一方針のため却下
- `nomic-embed-text`: 初期仕様（2026-03-19）で記載されていたが `sentence-transformers` に変更済み

---

## 4. `ALIASES_URL` / `NEKOCHAN_EMOJI_URL` の ref 統一

**決定**: 両 URL を `main`（短縮形）に統一する

**根拠**:
- `refs/heads/main` と `main` は GitHub Raw URL で同一コミットを指す
- `ALIASES_URL` が元々 `main` を使用していたため、`NEKOCHAN_EMOJI_URL` を合わせる
- 一貫性向上・URL 短縮

**実装済み変更**:
```python
# 変更前
NEKOCHAN_EMOJI_URL = "https://raw.githubusercontent.com/takanory/sphinx-nekochan/refs/heads/main/..."
# 変更後
NEKOCHAN_EMOJI_URL = "https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/..."
```

---

## 5. アノテーション生成プロンプト設計

**決定**: 英語 2〜3 文・感情/状況/用途を記述する固定フォーマットプロンプトを使用する

**根拠**:
- クエリはユーザーの日本語文章を `"query: "` プレフィックス付きで埋め込む
- アノテーションは `"passage: "` プレフィックス付きで埋め込む
- 英語アノテーション + 多言語モデルにより、日英クエリの両方に対応できる

**プロンプトテンプレート** (`_build_annotation_prompt`):
```
Write a short English description (2-3 sentences) for an emoji named '{emoji_name}'.
Also known as: {aliases}. The description should explain what the emoji looks like
and when to use it. Output only the description text, no extra formatting.
```

---

## 6. 再開ロジック（インクリメンタル保存）

**決定**: 各絵文字処理後に `annotations.json` を全件上書き保存する。再実行時は `existing_names` セットで既存エントリをスキップする。

**根拠**:
- 処理途中でクラッシュしても既処理分が保持される
- 実装シンプル（追記ではなく常に全件 JSON ダンプ）
- 378 件 × 小サイズ JSON → ファイルサイズ問題なし

---

## 7. デフォルト LLM モデル

**決定**: `qwen3.5:2b`（`DEFAULT_LLM_MODEL` 定数、`query.py` に定義）

**根拠**:
- マルチモーダル対応（PNG 画像 base64 を `images` フィールドで渡せる）
- `ollama pull qwen3.5:2b` で取得可能
- 明確化セッション（2026-05-02）で正式決定

**変更履歴**: `qwen2.5`（2026-03-19）→ `qwen3.5`（中間）→ `qwen3.5:2b`（2026-05-02 確定）

---

## 解決済み NEEDS CLARIFICATION 一覧

| 項目 | 解決方法 |
|------|----------|
| GIF スキップ後の報告 | stderr に `skipped_gif` リストを別メッセージで出力 |
| デフォルト LLM モデル名 | `qwen3.5:2b`（FR-007 も更新済み） |
| GIF の dry-run 扱い | dry-run でも GIF はスキップ（通常実行と同一挙動） |
| GIF がクエリ候補に出ないことの意図 | 一時的な制限（将来 GIF 対応モデルで再考） |
| URL の ref 統一 | `main` 短縮形に統一 |
