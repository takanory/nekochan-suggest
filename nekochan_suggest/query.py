"""埋め込みベクトル検索モジュール。

テキストクエリに対して、埋め込みベクトルを用いた類似絵文字検索を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path
import tomllib
from typing import cast


logger = logging.getLogger(__name__)

ANNOTATIONS_PATH = Path.home() / ".local" / "share" / "nekochan-suggest" / "annotations.json"
CONFIG_PATH = Path.home() / ".config" / "nekochan-suggest" / "config.toml"
DEFAULT_EMBED_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_LLM_MODEL = "qwen3.5:2b"


@dataclass
class SuggestionResult:
    """ネコチャン絵文字の提案結果 1 件。"""

    name: str
    score: float


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """2 つのベクトルのコサイン類似度を返す。"""
    if len(a) != len(b):
        logger.debug("ベクトル次元が一致しないため 0.0 を返します: %s != %s", len(a), len(b))
        return 0.0

    dot = sum(left * right for left, right in zip(a, b))
    magnitude_a = math.sqrt(sum(value * value for value in a))
    magnitude_b = math.sqrt(sum(value * value for value in b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return dot / (magnitude_a * magnitude_b)


def _load_annotations(path: Path) -> list[dict[str, object]]:
    """アノテーション JSON を読み込み、有効なレコードだけを返す。"""
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as file_obj:
        raw_records = json.load(file_obj)

    records: list[dict[str, object]] = []
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            continue
        name = raw_record.get("name")
        annotation = raw_record.get("annotation")
        embedding = raw_record.get("embedding")
        if not isinstance(name, str) or not isinstance(annotation, str):
            continue
        if not isinstance(embedding, list) or not embedding:
            continue
        records.append(raw_record)

    return records


def _load_config() -> dict[str, str]:
    """環境変数・設定ファイル・デフォルト値から設定を解決する。"""
    config_data: dict[str, object] = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as file_obj:
            config_data = tomllib.load(file_obj)

    embed_model = os.environ.get("NEKOCHAN_EMBED_MODEL") or config_data.get(
        "embed_model",
        DEFAULT_EMBED_MODEL,
    )
    llm_model = os.environ.get("NEKOCHAN_LLM_MODEL") or config_data.get(
        "llm_model",
        DEFAULT_LLM_MODEL,
    )
    ollama_url = os.environ.get("NEKOCHAN_OLLAMA_URL") or config_data.get(
        "ollama_url",
        "http://localhost:11434",
    )
    timeout = os.environ.get("NEKOCHAN_TIMEOUT") or config_data.get(
        "timeout",
        "30",
    )

    return {
        "embed_model": str(embed_model),
        "llm_model": str(llm_model),
        "ollama_url": str(ollama_url),
        "timeout": str(timeout),
    }


def _embed_text(text: str, embed_model: str) -> list[float]:
    """クエリテキストを埋め込みベクトルへ変換する。"""
    import sentence_transformers

    model = sentence_transformers.SentenceTransformer(embed_model)
    encoded = model.encode(f"query: {text}")
    vector = encoded.tolist() if hasattr(encoded, "tolist") else list(encoded)
    if not vector:
        raise ValueError("embedding result is empty")
    if isinstance(vector[0], list):
        raise ValueError("embedding result has unexpected shape")
    return [float(value) for value in vector]


def suggest(text: str, count: int = 3) -> list[SuggestionResult]:
    """テキストに対してネコチャン絵文字のファイル名を提案する。

    Args:
        text: 提案を求めるテキスト。
        count: 返す候補数（1〜10）。

    Returns:
        提案結果のリスト。
    """
    normalized_text = text.strip()
    if not normalized_text:
        raise ValueError("text is empty")
    if len(normalized_text) > 1000:
        raise ValueError("text is too long")
    if count < 1 or count > 10:
        raise ValueError("count is out of range")

    config = _load_config()
    embed_model = config["embed_model"]
    query_vector = _embed_text(normalized_text, embed_model)
    annotations = _load_annotations(ANNOTATIONS_PATH)

    scored_results = [
        SuggestionResult(
            name=str(record["name"]),
            score=_cosine_similarity(
                query_vector,
                cast(list[float], record["embedding"]),
            ),
        )
        for record in annotations
    ]
    scored_results.sort(key=lambda result: result.score, reverse=True)

    return scored_results[: min(count, len(scored_results))]
