"""テスト用フィクスチャ生成スクリプト。

tests/fixtures/annotations.json を生成する。
768 次元の決定論的な埋め込みベクトルを持つダミーレコードを作成する。

使い方:
    python tests/fixtures/gen_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

# 出力先
OUTPUT_PATH = Path(__file__).parent / "annotations.json"

# 768 次元のゼロベクトルを基底として、各レコードに固有の方向を持たせる
DIM = 768


def _make_embedding(index: int) -> list[float]:
    """決定論的な 768 次元の単位ベクトルを生成する。

    index 番目の次元のみ 1.0 にし、残りを 0.0 にする（標準基底ベクトル）。
    index が DIM を超える場合は最初の次元から繰り返す。
    """
    vec = [0.0] * DIM
    vec[index % DIM] = 1.0
    return vec


def _make_similar_embedding(index: int, noise_index: int) -> list[float]:
    """2 つの次元に値を持つ埋め込みベクトルを生成する（類似度テスト用）。

    主成分: index 番目の次元に 0.9
    副成分: noise_index 番目の次元に sqrt(1 - 0.9^2) ≈ 0.436
    合計ノルムが 1.0 になるように設定する。
    """
    import math

    vec = [0.0] * DIM
    vec[index % DIM] = 0.9
    vec[noise_index % DIM] = math.sqrt(1.0 - 0.9**2)
    return vec


# 正常レコード（embedding あり）
NORMAL_RECORDS = [
    {
        "name": "yatta-nya",
        "annotation": "A cat jumping with joy and excitement, expressing celebration and happiness.",
        "embedding": _make_embedding(0),
    },
    {
        "name": "niko-nya",
        "annotation": "A cat with a big smile, friendly and cheerful expression.",
        "embedding": _make_similar_embedding(0, 1),
    },
    {
        "name": "nemui-nya",
        "annotation": "A sleepy cat with half-closed eyes, looking tired and drowsy.",
        "embedding": _make_embedding(2),
    },
    {
        "name": "kyukei-nya",
        "annotation": "A cat taking a break, resting peacefully and relaxing.",
        "embedding": _make_similar_embedding(2, 3),
    },
    {
        "name": "hare-nya",
        "annotation": "A cat enjoying sunny weather, looking happy and relaxed outdoors.",
        "embedding": _make_embedding(4),
    },
    {
        "name": "okoru-nya",
        "annotation": "An angry cat with furrowed brows, expressing frustration or irritation.",
        "embedding": _make_embedding(5),
    },
]

# embedding フィールドが欠損したレコード（スキップテスト用）
MISSING_EMBEDDING_RECORD = {
    "name": "mystery-nya",
    "annotation": "A mysterious cat without embedding data.",
    # embedding フィールドなし
}

# embedding が空リストのレコード（スキップテスト用）
EMPTY_EMBEDDING_RECORD = {
    "name": "empty-nya",
    "annotation": "A cat with empty embedding.",
    "embedding": [],
}


def main() -> None:
    """annotations.json を生成して OUTPUT_PATH に書き込む。"""
    records = [
        *NORMAL_RECORDS,
        MISSING_EMBEDDING_RECORD,
        EMPTY_EMBEDDING_RECORD,
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"生成完了: {OUTPUT_PATH}")  # noqa: T201
    print(f"  正常レコード数: {len(NORMAL_RECORDS)}")  # noqa: T201
    print("  embedding 欠損レコード数: 1")  # noqa: T201
    print("  embedding 空レコード数: 1")  # noqa: T201
    print(f"  合計: {len(records)} レコード")  # noqa: T201


if __name__ == "__main__":
    main()
