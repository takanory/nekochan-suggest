"""CLIエントリーポイント・引数解析モジュール。

nekochan-suggest コマンドのメインエントリーポイントを提供する。
引数の解析と各サブコマンドへのディスパッチを担当する。
"""

from __future__ import annotations

import argparse
import sys

_SUBCOMMANDS = {"build-annotations"}


def _build_query_parser() -> argparse.ArgumentParser:
    """テキストクエリ用パーサーを構築して返す。"""
    parser = argparse.ArgumentParser(
        prog="nekochan-suggest",
        description="文章に対してネコチャン絵文字のファイル名を提案するツール。",
    )
    parser.add_argument(
        "text",
        nargs="?",
        metavar="TEXT",
        help="絵文字提案を求めるテキスト。省略時は標準入力から読み取る。",
    )
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=3,
        metavar="N",
        help="返す候補数（1〜10）。デフォルト: 3。",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="結果をJSON形式で標準出力に出力する。",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="N",
        help="LLMレスポンスのタイムアウト秒数。デフォルト: 30。",
    )
    return parser


def _build_build_annotations_parser() -> argparse.ArgumentParser:
    """build-annotations サブコマンド用パーサーを構築して返す。"""
    parser = argparse.ArgumentParser(
        prog="nekochan-suggest build-annotations",
        description="全絵文字のアノテーションを生成・保存する。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ファイルを保存せず、先頭3件のアノテーションをプレビュー表示する。",
    )
    return parser


def main() -> None:
    """CLIエントリーポイント。引数を解析して対応する処理を実行する。

    サブコマンド（build-annotations）が指定された場合はそちらへディスパッチし、
    それ以外はテキストクエリとして処理する。
    """
    # サブコマンドかテキストクエリかを先頭引数で判定する
    raw_args = sys.argv[1:]
    first = next((a for a in raw_args if not a.startswith("-")), None)

    if first is not None and first in _SUBCOMMANDS:
        idx = raw_args.index(first)
        sub_raw = raw_args[idx + 1 :]
        parser = _build_build_annotations_parser()
        args = parser.parse_args(sub_raw)
        _handle_build_annotations(args)
    else:
        parser = _build_query_parser()
        args = parser.parse_args(raw_args)
        _handle_query(args)


def _handle_build_annotations(args: argparse.Namespace) -> None:
    """build-annotations サブコマンドを処理する。

    Args:
        args: パース済みコマンドライン引数。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    print("未実装（別フィーチャー 001-nekochan-suggest で実装予定）")  # noqa: T201


def _handle_query(args: argparse.Namespace) -> None:
    """テキストクエリを処理して絵文字候補を返す。

    Args:
        args: パース済みコマンドライン引数。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
        --json フラグも同フィーチャーで実装予定。
    """
    # テキストの取得（引数または標準入力）
    text = args.text
    if text is None:
        if sys.stdin.isatty():
            print(  # noqa: T201
                "エラー: テキストを指定するか、標準入力からパイプで渡してください。",
                file=sys.stderr,
            )
            sys.exit(1)
        text = sys.stdin.read().strip()

    if not text:
        print(  # noqa: T201
            "エラー: テキストが空です。テキストを指定してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.json:
        print("未実装（別フィーチャー 001-nekochan-suggest で実装予定）")  # noqa: T201
    else:
        print("未実装（別フィーチャー 001-nekochan-suggest で実装予定）")  # noqa: T201


if __name__ == "__main__":
    main()
