"""アノテーション生成・ストレージモジュール。

sphinx-nekochan の絵文字に対するアノテーション（説明テキスト）の生成と
埋め込みベクトルの計算・永続化を担当する。
aliases.json を urllib でネットワーク取得し、Ollama API で各絵文字の
英語アノテーションを生成した後、sentence-transformers で埋め込みを生成して
JSON ファイルに保存する。
"""

from __future__ import annotations

import json
import logging
import sys
import urllib.request
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)

ALIASES_URL = "https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/aliases.json"
NEKOCHAN_EMOJI_URL = "https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/nekochan_emoji.json"


def fetch_aliases(url: str, timeout: int) -> dict[str, list[str]]:
    """aliases.json を urllib でネットワーク取得して返す。

    Args:
        url: aliases.json の取得先 URL。
        timeout: 接続タイムアウト秒数。

    Returns:
        {絵文字名: [エイリアス, ...]} の辞書。

    Raises:
        OSError: 接続エラーが発生した場合（そのまま伝播）。
        ValueError: HTTP ステータスが 200 以外の場合。
    """
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        raw = response.read()
    return cast(dict[str, list[str]], json.loads(raw))


def fetch_emoji_data(url: str, timeout: int) -> dict[str, dict[str, object]]:
    """nekochan_emoji.json を urllib でネットワーク取得して返す。

    Args:
        url: nekochan_emoji.json の取得先 URL。
        timeout: 接続タイムアウト秒数。

    Returns:
        {絵文字名: {"aliases": [...], "base64": "...", "mimetype": "..."}} の辞書。

    Raises:
        OSError: 接続エラーが発生した場合（そのまま伝播）。
        ValueError: HTTP ステータスが 200 以外の場合。
    """
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        raw = response.read()
    return cast(dict[str, dict[str, object]], json.loads(raw))


def _build_annotation_prompt(emoji_name: str, aliases: list[str]) -> str:
    """LLM へのアノテーション生成プロンプトを構築する（内部関数）。

    Args:
        emoji_name: 絵文字ファイル名（拡張子なし）。
        aliases: 絵文字の別名リスト。

    Returns:
        英語の LLM プロンプト文字列。
    """
    alias_part = f" Also known as: {', '.join(aliases)}." if aliases else ""
    return (
        f"Write a short English description (2-3 sentences) for an emoji named '{emoji_name}'.{alias_part} "
        "The description should explain what the emoji looks like and when to use it. "
        "Output only the description text, no extra formatting."
    )


def generate_annotation(
    emoji_name: str,
    aliases: list[str],
    ollama_url: str,
    llm_model: str,
    timeout: int,
    image_base64: str = "",
) -> str:
    """Ollama API を呼び出して絵文字のアノテーションテキストを生成する。

    image_base64 が指定された場合、Ollama のマルチモーダル機能を使って
    画像をモデルに渡す（images フィールド）。

    Args:
        emoji_name: 絵文字ファイル名（拡張子なし）。
        aliases: 絵文字の別名リスト。
        ollama_url: Ollama サーバーのベース URL。
        llm_model: 使用する LLM モデル名。
        timeout: HTTP タイムアウト秒数。
        image_base64: 絵文字画像の base64 文字列。空文字列の場合は画像なしで呼び出す。

    Returns:
        生成されたアノテーションテキスト。

    Raises:
        OSError: 接続エラーが発生した場合（そのまま伝播）。
        TimeoutError: タイムアウトした場合（そのまま伝播）。
    """
    prompt = _build_annotation_prompt(emoji_name, aliases)
    body: dict[str, object] = {"model": llm_model, "prompt": prompt, "stream": False}
    if image_base64:
        body["images"] = [image_base64]
    payload = json.dumps(body).encode()
    req = urllib.request.Request(  # noqa: S310
        f"{ollama_url}/api/generate",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310
        result = json.loads(response.read())
    return str(result["response"])


def generate_embedding(text: str, embed_model: str) -> list[float]:
    """sentence-transformers でテキストの埋め込みベクトルを生成する。

    passage: プレフィックスを付与してエンコードする（build-annotations 用）。

    Args:
        text: 埋め込みを生成するテキスト。
        embed_model: 使用する埋め込みモデル名。

    Returns:
        埋め込みベクトル（float のリスト）。
    """
    import sentence_transformers

    model = sentence_transformers.SentenceTransformer(embed_model)
    encoded = model.encode(f"passage: {text}")
    return cast(list[float], encoded.tolist())


def load_existing_annotations(path: Path) -> list[dict[str, object]]:
    """既存のアノテーション JSON ファイルを読み込む。

    Args:
        path: annotations.json のパス。

    Returns:
        既存レコードのリスト。ファイルが存在しない場合は空リスト。
    """
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return cast(list[dict[str, object]], json.load(f))


def save_annotations_file(records: list[dict[str, object]], path: Path) -> None:
    """アノテーションレコードを JSON ファイルに上書き保存する。

    親ディレクトリが存在しない場合は自動作成する。

    Args:
        records: 保存するレコードのリスト。
        path: 保存先ファイルパス。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def build_all_annotations(dry_run: bool, config: dict[str, str]) -> None:  # noqa: FBT001
    """全絵文字のアノテーションを生成・保存する。

    aliases.json を取得してすべての絵文字に対してアノテーションと埋め込みを
    生成し、annotations.json に 1 件ごと上書き保存する。
    既存エントリは再生成せずスキップする（再開ロジック）。
    1 件の処理エラーはログに記録してスキップし、処理を継続する。

    Args:
        dry_run: True の場合、先頭 3 件のプレビューのみ stdout に出力し
                 ファイルへの書き込みを行わない。
        config: _load_config() が返す設定辞書。
                必須キー: ollama_url, llm_model, embed_model, timeout。

    Raises:
        ValueError: aliases.json の取得に失敗した場合（OSError を含む）。
    """
    from .query import ANNOTATIONS_PATH

    ollama_url = config["ollama_url"]
    llm_model = config["llm_model"]
    embed_model = config["embed_model"]
    timeout = int(config["timeout"])

    # aliases.json 取得（OSError は ValueError にラップ）
    try:
        aliases_dict = fetch_aliases(ALIASES_URL, timeout)
    except OSError as e:
        raise ValueError(f"failed to fetch aliases.json from {ALIASES_URL}: {e}") from e

    # nekochan_emoji.json 取得（OSError は ValueError にラップ）
    try:
        emoji_data = fetch_emoji_data(NEKOCHAN_EMOJI_URL, timeout)
    except OSError as e:
        raise ValueError(f"failed to fetch nekochan_emoji.json from {NEKOCHAN_EMOJI_URL}: {e}") from e

    existing_records = load_existing_annotations(ANNOTATIONS_PATH)
    existing_names = {str(r["name"]) for r in existing_records}
    records: list[dict[str, object]] = list(existing_records)
    skipped: list[str] = []
    total = len(aliases_dict)
    dry_run_count = 0

    for i, (name, alias_list) in enumerate(aliases_dict.items()):
        # 進行表示（stderr）
        sys.stderr.write(f"[{i + 1}/{total}] {name}\r")
        sys.stderr.flush()

        if name in existing_names:
            continue

        emoji_entry = emoji_data.get(name, {})
        image_b64 = str(emoji_entry.get("base64", ""))

        try:
            annotation = generate_annotation(name, alias_list, ollama_url, llm_model, timeout, image_b64)
            embedding = generate_embedding(annotation, embed_model)
        except Exception as e:  # noqa: BLE001
            logger.warning("絵文字 '%s' の処理をスキップしました: %s", name, e)
            skipped.append(name)
            continue

        record: dict[str, object] = {
            "name": name,
            "annotation": annotation,
            "embedding": embedding,
            "image_base64": emoji_entry.get("base64", ""),
            "image_mimetype": emoji_entry.get("mimetype", ""),
        }

        if dry_run:
            if dry_run_count < 3:
                print(json.dumps(record, ensure_ascii=False))  # noqa: T201
                dry_run_count += 1
            if dry_run_count >= 3:
                break
            continue

        records.append(record)
        save_annotations_file(records, ANNOTATIONS_PATH)

    # 改行で進行表示をクリア
    sys.stderr.write("\n")
    sys.stderr.flush()

    if skipped:
        sys.stderr.write(f"Skipped {len(skipped)} emojis due to errors: {', '.join(skipped)}\n")
        sys.stderr.flush()

