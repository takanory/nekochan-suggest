"""アノテーション生成・ストレージモジュール。

sphinx-nekochan の絵文字に対するアノテーション（説明テキスト・タグ等）の
生成と永続化を担当する。
ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
"""

from __future__ import annotations

from pathlib import Path


def generate_annotation(emoji_name: str) -> str:
    """絵文字名からアノテーションテキストを生成する。

    Args:
        emoji_name: 絵文字ファイル名（拡張子なし）。

    Returns:
        生成されたアノテーションテキスト。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    raise NotImplementedError("別フィーチャー 001-nekochan-suggest で実装予定")


def save_annotations(annotations: dict[str, str], output_dir: Path) -> None:
    """アノテーション辞書をファイルシステムに保存する。

    Args:
        annotations: {絵文字名: アノテーションテキスト} の辞書。
        output_dir: 保存先ディレクトリ。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    raise NotImplementedError("別フィーチャー 001-nekochan-suggest で実装予定")


def load_annotations(input_dir: Path) -> dict[str, str]:
    """ファイルシステムからアノテーション辞書を読み込む。

    Args:
        input_dir: 読み込み元ディレクトリ。

    Returns:
        {絵文字名: アノテーションテキスト} の辞書。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    raise NotImplementedError("別フィーチャー 001-nekochan-suggest で実装予定")


def build_all_annotations(dry_run: bool = False) -> dict[str, str]:
    """全絵文字のアノテーションを生成する。

    Args:
        dry_run: True の場合、先頭3件のプレビューのみ返しファイルを保存しない。

    Returns:
        {絵文字名: アノテーションテキスト} の辞書。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    raise NotImplementedError("別フィーチャー 001-nekochan-suggest で実装予定")
