"""アノテーション生成・ストレージモジュール。

sphinx-nekochan の絵文字に対するアノテーション（説明テキスト）の生成と
埋め込みベクトルの計算・永続化を担当する。
aliases.json を urllib でネットワーク取得し、Ollama API で各絵文字の
英語アノテーションを生成した後、sentence-transformers で埋め込みを生成して
JSON ファイルに保存する。
"""

from __future__ import annotations

import base64
import io
import json
import logging
import sys
import urllib.request
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)

ALIASES_URL = "https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/aliases.json"
NEKOCHAN_EMOJI_URL = "https://raw.githubusercontent.com/takanory/sphinx-nekochan/main/sphinx_nekochan/data/nekochan_emoji.json"


def gif_first_frame_as_png_base64(gif_base64: str) -> str:
    """GIF base64 の最初のフレームを PNG に変換し base64 で返す。

    .. deprecated::
        代わりに ``gif_frames_as_png_base64_list(gif_base64, 1)`` を使用すること。

    Args:
        gif_base64: GIF 画像の base64 文字列。

    Returns:
        1 枚目フレームを PNG 変換した base64 文字列。
    """
    frames = gif_frames_as_png_base64_list(gif_base64, max_frames=1)
    return frames[0]


def gif_frames_as_png_base64_list(gif_base64: str, max_frames: int) -> list[str]:
    """GIF base64 から複数フレームを PNG base64 リストとして返す。

    max_frames が GIF の総フレーム数を超える場合は全フレームを返す。
    フレームインデックスは均等間隔サンプリング（先頭・末尾を含む）で算出する。
    サンプリング式: ``i * (total - 1) // (N - 1)`` (i = 0, 1, ..., N-1)
    N=1 の特殊ケースではインデックス 0 のみを使用する。

    Args:
        gif_base64: GIF 画像の base64 文字列。
        max_frames: 抽出する最大フレーム数。1 以上でなければならない。

    Returns:
        PNG 変換済みフレームの base64 文字列リスト（長さ: 1 ≤ n ≤ max_frames）。

    Raises:
        Exception: 壊れた GIF など Pillow が読み込めない場合（そのまま伝播）。
    """
    from PIL import Image

    gif_bytes = base64.b64decode(gif_base64)
    with Image.open(io.BytesIO(gif_bytes)) as img:
        n_frames = getattr(img, "n_frames", 1)
        # 抽出するフレームインデックスを均等間隔で算出
        actual = min(max_frames, n_frames)
        if actual <= 1:
            indices = [0]
        else:
            indices = [i * (n_frames - 1) // (actual - 1) for i in range(actual)]

        result: list[str] = []
        for idx in indices:
            img.seek(idx)
            frame = img.convert("RGBA")
            buf = io.BytesIO()
            frame.save(buf, format="PNG")
            result.append(base64.b64encode(buf.getvalue()).decode())

    return result


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


def _build_annotation_prompt(
    emoji_name: str, aliases: list[str], gif_frame_count: int = 0
) -> str:
    """LLM へのアノテーション生成プロンプトを構築する（内部関数）。

    gif_frame_count > 1 の場合、プロンプト先頭にアニメーションである旨を追記する。

    Args:
        emoji_name: 絵文字ファイル名（拡張子なし）。
        aliases: 絵文字の別名リスト。
        gif_frame_count: GIF から抽出したフレーム数。0 または 1 の場合は追記しない。

    Returns:
        英語の LLM プロンプト文字列。
    """
    alias_part = f" Also known as: {', '.join(aliases)}." if aliases else ""
    gif_prefix = (
        f"These are {gif_frame_count} frames from an animated GIF emoji. "
        if gif_frame_count > 1
        else ""
    )
    return (
        f"{gif_prefix}Write a short English description (2-3 sentences) for an emoji named '{emoji_name}'.{alias_part} "
        "The description should explain what the emoji looks like and when to use it. "
        "Output only the description text, no extra formatting."
    )


def generate_annotation(
    emoji_name: str,
    aliases: list[str],
    ollama_url: str,
    llm_model: str,
    timeout: int,
    images: list[str] | None = None,
    gif_frame_count: int = 0,
) -> str:
    """Ollama API を呼び出して絵文字のアノテーションテキストを生成する。

    images が指定された場合、Ollama のマルチモーダル機能を使って
    画像シーケンスをモデルに渡す（images フィールド）。
    gif_frame_count > 1 のとき、プロンプト先頭にアニメーション旨を追記する。

    Args:
        emoji_name: 絵文字ファイル名（拡張子なし）。
        aliases: 絵文字の別名リスト。
        ollama_url: Ollama サーバーのベース URL。
        llm_model: 使用する LLM モデル名。
        timeout: HTTP タイムアウト秒数。
        images: 絵文字画像の base64 文字列リスト。None または空の場合は画像なしで呼び出す。
        gif_frame_count: GIF から抽出したフレーム数。プロンプト修飾に使用。

    Returns:
        生成されたアノテーションテキスト。

    Raises:
        OSError: 接続エラーが発生した場合（そのまま伝播）。
        TimeoutError: タイムアウトした場合（そのまま伝播）。
    """
    prompt = _build_annotation_prompt(
        emoji_name, aliases, gif_frame_count=gif_frame_count
    )
    body: dict[str, object] = {"model": llm_model, "prompt": prompt, "stream": False}
    if images:
        body["images"] = images
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
    GIF 以外の既存エントリは再生成せずスキップする（再開ロジック）。
    GIF の既存エントリはマルチフレーム方式で上書き再生成する（FR-012）。
    1 件の処理エラーはログに記録してスキップし、処理を継続する。

    Args:
        dry_run: True の場合、先頭 3 件のプレビューのみ stdout に出力し
                 ファイルへの書き込みを行わない。
        config: _load_config() が返す設定辞書。
                必須キー: ollama_url, llm_model, embed_model, timeout, gif_max_frames。

    Raises:
        ValueError: aliases.json の取得に失敗した場合（OSError を含む）。
    """
    from .query import ANNOTATIONS_PATH

    ollama_url = config["ollama_url"]
    llm_model = config["llm_model"]
    embed_model = config["embed_model"]
    timeout = int(config["timeout"])

    # gif_max_frames のバリデーション（デフォルト 4）
    _default_gif_max = 4
    try:
        gif_max_frames = int(config.get("gif_max_frames", str(_default_gif_max)))
        if gif_max_frames <= 0:
            logger.warning(
                "gif_max_frames=%s は無効（1 以上でなければならない）。デフォルト %d を使用します。",
                config.get("gif_max_frames"),
                _default_gif_max,
            )
            gif_max_frames = _default_gif_max
    except (ValueError, TypeError):
        logger.warning(
            "gif_max_frames='%s' は整数に変換できません。デフォルト %d を使用します。",
            config.get("gif_max_frames"),
            _default_gif_max,
        )
        gif_max_frames = _default_gif_max

    # aliases.json 取得（OSError は ValueError にラップ）
    try:
        aliases_dict = fetch_aliases(ALIASES_URL, timeout)
    except OSError as e:
        raise ValueError(f"failed to fetch aliases.json from {ALIASES_URL}: {e}") from e

    # nekochan_emoji.json 取得（OSError は ValueError にラップ）
    try:
        emoji_data = fetch_emoji_data(NEKOCHAN_EMOJI_URL, timeout)
    except OSError as e:
        raise ValueError(
            f"failed to fetch nekochan_emoji.json from {NEKOCHAN_EMOJI_URL}: {e}"
        ) from e

    existing_records = load_existing_annotations(ANNOTATIONS_PATH)
    # GIF 既存エントリは再生成対象のためスキップしない（FR-012）
    existing_names = {
        str(r["name"])
        for r in existing_records
        if str(r.get("image_mimetype", "")) != "image/gif"
    }
    records: list[dict[str, object]] = [
        r for r in existing_records if str(r.get("image_mimetype", "")) != "image/gif"
    ]
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
        mimetype = str(emoji_entry.get("mimetype", ""))
        image_b64 = str(emoji_entry.get("base64", ""))

        # GIF は複数フレームを PNG リストに変換して LLM に渡す
        if mimetype == "image/gif" and image_b64:
            try:
                frames = gif_frames_as_png_base64_list(image_b64, gif_max_frames)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "絵文字 '%s' の GIF フレーム抽出をスキップしました: %s", name, e
                )
                skipped.append(name)
                continue
            logger.debug("Extracted %d frames from gif: %s", len(frames), name)
            images: list[str] | None = frames
            gif_frame_count = len(frames)
        elif image_b64:
            # PNG/JPEG 等は単一要素リストとして渡す
            images = [image_b64]
            gif_frame_count = 0
        else:
            images = None
            gif_frame_count = 0

        try:
            annotation = generate_annotation(
                name,
                alias_list,
                ollama_url,
                llm_model,
                timeout,
                images=images,
                gif_frame_count=gif_frame_count,
            )
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
        sys.stderr.write(
            f"Skipped {len(skipped)} emojis due to errors: {', '.join(skipped)}\n"
        )
        sys.stderr.flush()
