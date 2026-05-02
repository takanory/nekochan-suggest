"""CLIエントリーポイント・引数解析モジュール。

nekochan-suggest コマンドのメインエントリーポイントを提供する。
引数の解析と各サブコマンドへのディスパッチを担当する。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import NoReturn

from .query import SuggestionResult, _load_config, suggest

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

    """
    text = _resolve_query_text(args)
    _validate_query_args(text, args.count)

    embed_model = _load_config()["embed_model"]
    if not _is_model_cached(embed_model):
        print(f"Downloading model {embed_model}...", file=sys.stderr)  # noqa: T201

    try:
        results = suggest(text, count=args.count)
    except FileNotFoundError:
        _exit_with_error(
            "Error: annotations file not found. Run 'nekochan-suggest build-annotations' first."
        )
    except OSError:
        _exit_with_error(f"Error: failed to load embedding model '{embed_model}'.")
    except RuntimeError as exc:
        _exit_with_error(f"Error: embedding failed: {exc}")
    except ValueError:
        _exit_with_error("Error: unexpected embedding result. Check embed_model setting.")

    if args.json:
        print(json.dumps({"suggestions": [_to_json_result(result) for result in results]}, ensure_ascii=False))  # noqa: T201
        return

    for index, result in enumerate(results, start=1):
        print(f"{index}. {result.name}  {result.score:.2f}")  # noqa: T201


def _resolve_query_text(args: argparse.Namespace) -> str:
    """CLI 引数または標準入力から検索テキストを解決する。"""
    if args.text is not None:
        return args.text
    if sys.stdin.isatty():
        _exit_with_error("Error: provide text as an argument or pipe it via stdin.")
    return sys.stdin.read().strip()


def _validate_query_args(text: str, count: int) -> None:
    """CLI 層の入力バリデーションを行う。"""
    if not text.strip():
        _exit_with_error("Error: text is empty.")
    if len(text.strip()) > 1000:
        _exit_with_error("Error: text is too long (max 1000 characters).")
    if count < 1 or count > 10:
        _exit_with_error("Error: --count out of range (1-10).")


def _resolve_model_cache_path(model_name: str) -> Path:
    """Hugging Face Hub のモデルキャッシュパスを返す。"""
    hub_root = Path(
        os.environ.get(
            "HUGGINGFACE_HUB_CACHE",
            str(Path(os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface"))) / "hub"),
        )
    )
    return hub_root / f"models--{model_name.replace('/', '--')}"


def _is_model_cached(model_name: str) -> bool:
    """指定モデルのキャッシュがすでに存在するかを返す。"""
    return _resolve_model_cache_path(model_name).exists()


def _to_json_result(result: SuggestionResult) -> dict[str, float | str]:
    """SuggestionResult を JSON 互換 dict に変換する。"""
    return {"name": result.name, "score": result.score}


def _exit_with_error(message: str) -> NoReturn:
    """エラーメッセージを stderr に出力して終了する。"""
    print(message, file=sys.stderr)  # noqa: T201
    raise SystemExit(1)


if __name__ == "__main__":
    main()
