"""埋め込みベクトル検索モジュール。

テキストクエリに対して、埋め込みベクトルを用いた類似絵文字検索を提供する。
ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
"""

from __future__ import annotations


def embed_text(text: str) -> list[float]:
    """テキストを埋め込みベクトルに変換する。

    Args:
        text: 埋め込み対象のテキスト。

    Returns:
        埋め込みベクトル（浮動小数点数のリスト）。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    raise NotImplementedError("別フィーチャー 001-nekochan-suggest で実装予定")


def search_similar(
    query_vector: list[float],
    top_k: int = 3,
) -> list[tuple[str, float]]:
    """クエリベクトルに対して類似度の高い絵文字を返す。

    Args:
        query_vector: クエリの埋め込みベクトル。
        top_k: 返す候補数。

    Returns:
        (絵文字ファイル名, 類似スコア) のリスト。スコア降順。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    raise NotImplementedError("別フィーチャー 001-nekochan-suggest で実装予定")


def suggest(text: str, count: int = 3, timeout: int = 30) -> list[str]:
    """テキストに対してネコチャン絵文字のファイル名を提案する。

    Args:
        text: 提案を求めるテキスト。
        count: 返す候補数（1〜10）。
        timeout: LLMレスポンスのタイムアウト秒数。

    Returns:
        絵文字ファイル名のリスト。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    raise NotImplementedError("別フィーチャー 001-nekochan-suggest で実装予定")
