"""CLI エントリーポイントの基本動作テスト。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from nekochan_suggest.cli import _handle_query
from nekochan_suggest.cli import (
    _build_query_parser,
    _build_build_annotations_parser,
    _handle_build_annotations,
    _is_model_cached,
    _resolve_model_cache_path,
    _resolve_query_text,
    main,
)
from nekochan_suggest.query import SuggestionResult


def test_package_import() -> None:
    """パッケージのインポートがエラーなく完了することを確認する。"""
    import nekochan_suggest  # noqa: F401

    assert nekochan_suggest.__version__ == "0.1.0"


def test_cli_help_exits_zero() -> None:
    """--help オプションが終了コード 0 で完了することを確認する。"""
    result = subprocess.run(
        [sys.executable, "-m", "nekochan_suggest.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"終了コードが 0 でない: {result.stderr}"


def test_cli_help_contains_options() -> None:
    """--help の出力に必須オプションが含まれることを確認する。"""
    result = subprocess.run(
        [sys.executable, "-m", "nekochan_suggest.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert "--count" in result.stdout, "--count オプションが表示されていない"
    assert "--json" in result.stdout, "--json オプションが表示されていない"
    assert "--timeout" not in result.stdout, "--timeout オプションが残っている"


def test_cli_build_annotations_recognized() -> None:
    """build-annotations サブコマンドが認識されることを確認する。"""
    result = subprocess.run(
        [sys.executable, "-m", "nekochan_suggest.cli", "build-annotations"],
        capture_output=True,
        text=True,
    )
    # サブコマンドとして認識されれば終了コード 0、エラーなら 2 になる
    assert result.returncode == 0, (
        f"build-annotations が認識されていない: {result.stderr}"
    )


@pytest.mark.integration
def test_cli_text_stub_response() -> None:
    """テキスト引数に対して CLI がアノテーションエラーを出力することを確認する。"""
    result = subprocess.run(
        [sys.executable, "-m", "nekochan_suggest.cli", "テスト入力"],
        capture_output=True,
        text=True,
    )
    # アノテーションファイルが不在のため終了コード 1 と適切なエラーを返す
    assert result.returncode == 1, f"終了コードが 1 でない: {result.stderr}"
    assert "annotations file not found" in result.stderr, "期待するエラーメッセージが含まれない"


def test_handle_query_formats_text_output(capsys: pytest.CaptureFixture[str]) -> None:
    """通常出力は順位・名前・小数点 2 桁のスコアで表示する。"""
    args = argparse.Namespace(text="おはよう", count=3, json=False)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
        "nekochan_suggest.cli.suggest",
        return_value=[
            SuggestionResult("yatta-nya", 0.8734567),
            SuggestionResult("niko-nya", 0.8213456),
        ],
    ):
        _handle_query(args)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["1. yatta-nya  0.87", "2. niko-nya  0.82"]


def test_handle_query_formats_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    """JSON 出力は score を丸めずに返す。"""
    args = argparse.Namespace(text="おはよう", count=3, json=True)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
        "nekochan_suggest.cli.suggest",
        return_value=[SuggestionResult("nemui-nya", 0.9123456)],
    ):
        _handle_query(args)

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {"suggestions": [{"name": "nemui-nya", "score": 0.9123456}]}


def test_handle_query_passes_explicit_count() -> None:
    """--count 指定値を suggest() に渡す。"""
    args = argparse.Namespace(text="おはよう", count=5, json=False)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
        "nekochan_suggest.cli.suggest",
        return_value=[],
    ) as mock_suggest:
        _handle_query(args)

    mock_suggest.assert_called_once_with("おはよう", count=5)


def test_handle_query_prefers_cli_argument_over_stdin(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI 引数がある場合は stdin を読まない。"""
    args = argparse.Namespace(text="CLI入力", count=3, json=False)

    with patch("sys.stdin", StringIO("stdin入力")):
        with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
            "nekochan_suggest.cli.suggest",
            return_value=[SuggestionResult("hare-nya", 0.8)],
        ) as mock_suggest:
            _handle_query(args)

    captured = capsys.readouterr()
    assert "hare-nya" in captured.out
    mock_suggest.assert_called_once_with("CLI入力", count=3)


@pytest.mark.parametrize(
    ("text", "count", "message"),
    [
        ("", 3, "Error: text is empty."),
        ("   ", 3, "Error: text is empty."),
        ("a" * 1001, 3, "Error: text is too long (max 1000 characters)."),
        ("ok", 0, "Error: --count out of range (1-10)."),
        ("ok", 11, "Error: --count out of range (1-10)."),
    ],
)
def test_handle_query_validation_errors(
    text: str,
    count: int,
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """入力バリデーションエラーは stderr と exit code 1 になる。"""
    args = argparse.Namespace(text=text, count=count, json=False)

    with pytest.raises(SystemExit) as exc_info:
        _handle_query(args)

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert captured.err.strip() == message


def test_handle_query_missing_annotations_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """アノテーションファイル不在時のエラーを整形する。"""
    args = argparse.Namespace(text="ok", count=3, json=False)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
        "nekochan_suggest.cli.suggest",
        side_effect=FileNotFoundError,
    ):
        with pytest.raises(SystemExit) as exc_info:
            _handle_query(args)

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert (
        captured.err.strip()
        == "Error: annotations file not found. Run 'nekochan-suggest build-annotations' first."
    )


@pytest.mark.integration
def test_cli_tty_stdin_error_path() -> None:
    """TTY かつ TEXT 未指定時は英語エラーで終了する。"""
    command = """
from io import StringIO
import sys
from nekochan_suggest import cli

class TtyStdin(StringIO):
    def isatty(self):
        return True

sys.stdin = TtyStdin("")
cli.main()
"""
    result = subprocess.run(
        [sys.executable, "-c", command],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stderr.strip() == "Error: provide text as an argument or pipe it via stdin."


@pytest.mark.integration
def test_cli_stdin_pipe_success_path() -> None:
    """stdin パイプ入力で正常に候補を返す。"""
    command = """
from io import StringIO
import sys
from unittest.mock import patch
from nekochan_suggest import cli
from nekochan_suggest.query import SuggestionResult

class PipeStdin(StringIO):
    def isatty(self):
        return False

sys.stdin = PipeStdin("おはよう")

with patch(
    'nekochan_suggest.cli.suggest',
    return_value=[
        SuggestionResult('yatta-nya', 0.9),
        SuggestionResult('niko-nya', 0.8),
        SuggestionResult('hare-nya', 0.7),
    ],
):
    cli.main()
"""
    result = subprocess.run(
        [sys.executable, "-c", command],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "1. yatta-nya  0.90",
        "2. niko-nya  0.80",
        "3. hare-nya  0.70",
    ]


# ---- カバレッジ補完テスト ----


def test_build_query_parser_returns_parser() -> None:
    """_build_query_parser が有効なパーサーを返す。"""
    parser = _build_query_parser()
    args = parser.parse_args(["おはよう"])
    assert args.text == "おはよう"
    assert args.count == 3
    assert args.json is False


def test_build_query_parser_count_flag() -> None:
    """_build_query_parser が --count フラグを解釈する。"""
    parser = _build_query_parser()
    args = parser.parse_args(["--count", "5", "テキスト"])
    assert args.count == 5


def test_build_build_annotations_parser_returns_parser() -> None:
    """_build_build_annotations_parser が有効なパーサーを返す。"""
    parser = _build_build_annotations_parser()
    args = parser.parse_args([])
    assert args.dry_run is False


def test_main_dispatches_query(capsys: pytest.CaptureFixture[str]) -> None:
    """main() がクエリサブコマンドを _handle_query へディスパッチする。"""
    with patch("sys.argv", ["nekochan-suggest", "おはよう"]), patch(
        "nekochan_suggest.cli._handle_query"
    ) as mock_handle:
        main()
    mock_handle.assert_called_once()


def test_main_dispatches_build_annotations(capsys: pytest.CaptureFixture[str]) -> None:
    """main() が build-annotations を _handle_build_annotations へディスパッチする。"""
    with patch("sys.argv", ["nekochan-suggest", "build-annotations"]), patch(
        "nekochan_suggest.cli._handle_build_annotations"
    ) as mock_handle:
        main()
    mock_handle.assert_called_once()


def test_handle_build_annotations_calls_build(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """_handle_build_annotations が build_all_annotations を呼び出す。"""
    args = argparse.Namespace(dry_run=False, timeout=None)
    with (
        patch("nekochan_suggest.cli.build_all_annotations") as mock_build,
        patch("nekochan_suggest.cli._load_config", return_value={
            "ollama_url": "http://localhost:11434",
            "llm_model": "qwen3.5",
            "embed_model": "intfloat/multilingual-e5-base",
            "timeout": "30",
        }),
    ):
        _handle_build_annotations(args)
    mock_build.assert_called_once()


def test_handle_query_prints_model_download_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """モデル未キャッシュ時に stderr へダウンロードメッセージを出力する。"""
    args = argparse.Namespace(text="おはよう", count=3, json=False)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=False), patch(
        "nekochan_suggest.cli.suggest",
        return_value=[SuggestionResult("yatta-nya", 0.9)],
    ), patch("nekochan_suggest.cli._load_config", return_value={"embed_model": "intfloat/multilingual-e5-base"}):
        _handle_query(args)

    captured = capsys.readouterr()
    assert "Downloading model" in captured.err


def test_handle_query_oserror(capsys: pytest.CaptureFixture[str]) -> None:
    """suggest() が OSError を投げた場合に適切なエラーを返す。"""
    args = argparse.Namespace(text="ok", count=3, json=False)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
        "nekochan_suggest.cli.suggest",
        side_effect=OSError("network error"),
    ), patch("nekochan_suggest.cli._load_config", return_value={"embed_model": "intfloat/multilingual-e5-base"}):
        with pytest.raises(SystemExit) as exc_info:
            _handle_query(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "failed to load embedding model" in captured.err


def test_handle_query_runtime_error(capsys: pytest.CaptureFixture[str]) -> None:
    """suggest() が RuntimeError を投げた場合に適切なエラーを返す。"""
    args = argparse.Namespace(text="ok", count=3, json=False)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
        "nekochan_suggest.cli.suggest",
        side_effect=RuntimeError("encode failed"),
    ), patch("nekochan_suggest.cli._load_config", return_value={"embed_model": "intfloat/multilingual-e5-base"}):
        with pytest.raises(SystemExit) as exc_info:
            _handle_query(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "embedding failed" in captured.err


def test_handle_query_value_error(capsys: pytest.CaptureFixture[str]) -> None:
    """suggest() が ValueError を投げた場合に適切なエラーを返す。"""
    args = argparse.Namespace(text="ok", count=3, json=False)

    with patch("nekochan_suggest.cli._is_model_cached", return_value=True), patch(
        "nekochan_suggest.cli.suggest",
        side_effect=ValueError("empty embedding"),
    ), patch("nekochan_suggest.cli._load_config", return_value={"embed_model": "intfloat/multilingual-e5-base"}):
        with pytest.raises(SystemExit) as exc_info:
            _handle_query(args)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "unexpected embedding result" in captured.err


def test_resolve_query_text_from_stdin(capsys: pytest.CaptureFixture[str]) -> None:
    """stdin 非 TTY の場合は stdin からテキストを読み込む。"""
    args = argparse.Namespace(text=None, count=3, json=False)

    with patch("sys.stdin", StringIO("stdin テキスト")) as mock_stdin:
        mock_stdin.isatty = lambda: False  # type: ignore[method-assign]
        text = _resolve_query_text(args)

    assert text == "stdin テキスト"


def test_resolve_model_cache_path_default() -> None:
    """デフォルト設定でキャッシュパスが正しく生成される。"""
    path = _resolve_model_cache_path("intfloat/multilingual-e5-base")
    assert "models--intfloat--multilingual-e5-base" in str(path)


def test_is_model_cached_returns_false_for_nonexistent(tmp_path: pytest.TempPathFactory) -> None:
    """存在しないモデルは False を返す。"""
    with patch("nekochan_suggest.cli._resolve_model_cache_path", return_value=tmp_path / "nonexistent"):
        result = _is_model_cached("some-model")
    assert result is False


# ---------------------------------------------------------------------------
# T007: _handle_build_annotations() テスト
# ---------------------------------------------------------------------------


class TestHandleBuildAnnotations:
    """_handle_build_annotations() の単体テスト。"""

    def _make_args(self, dry_run: bool = False, timeout: int | None = None) -> argparse.Namespace:
        return argparse.Namespace(dry_run=dry_run, timeout=timeout)

    def test_dry_run_calls_build_with_dry_run_true(self) -> None:
        """--dry-run フラグで build_all_annotations(dry_run=True, config=...) が呼ばれる。"""
        with (
            patch("nekochan_suggest.cli.build_all_annotations") as mock_build,
            patch("nekochan_suggest.cli._load_config", return_value={
                "ollama_url": "http://localhost:11434",
                "llm_model": "qwen3.5",
                "embed_model": "intfloat/multilingual-e5-base",
                "timeout": "30",
            }),
        ):
            _handle_build_annotations(self._make_args(dry_run=True))

        mock_build.assert_called_once()
        call_kwargs = mock_build.call_args
        assert call_kwargs.kwargs.get("dry_run") is True or call_kwargs.args[0] is True

    def test_timeout_arg_overrides_config(self) -> None:
        """--timeout 60 で config['timeout'] が '60' に上書きされる。"""
        captured_config: dict = {}

        def capture_build(dry_run: bool, config: dict) -> None:  # noqa: FBT001
            captured_config.update(config)

        with (
            patch("nekochan_suggest.cli.build_all_annotations", side_effect=capture_build),
            patch("nekochan_suggest.cli._load_config", return_value={
                "ollama_url": "http://localhost:11434",
                "llm_model": "qwen3.5",
                "embed_model": "intfloat/multilingual-e5-base",
                "timeout": "30",
            }),
        ):
            _handle_build_annotations(self._make_args(timeout=60))

        assert captured_config["timeout"] == "60"

    def test_value_error_from_fetch_exits_with_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        """aliases fetch 失敗（ValueError）で stderr にエラーメッセージ、終了コード 1。"""
        with (
            patch("nekochan_suggest.cli.build_all_annotations", side_effect=ValueError("HTTP 404")),
            patch("nekochan_suggest.cli._load_config", return_value={
                "ollama_url": "http://localhost:11434",
                "llm_model": "qwen3.5",
                "embed_model": "intfloat/multilingual-e5-base",
                "timeout": "30",
            }),
            pytest.raises(SystemExit) as exc_info,
        ):
            _handle_build_annotations(self._make_args())

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: failed to fetch aliases.json:" in captured.err

    def test_oserror_from_ollama_exits_with_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Ollama 未起動（OSError）で stderr にエラーメッセージ、終了コード 1。"""
        with (
            patch("nekochan_suggest.cli.build_all_annotations", side_effect=OSError("connection refused")),
            patch("nekochan_suggest.cli._load_config", return_value={
                "ollama_url": "http://localhost:11434",
                "llm_model": "qwen3.5",
                "embed_model": "intfloat/multilingual-e5-base",
                "timeout": "30",
            }),
            pytest.raises(SystemExit) as exc_info,
        ):
            _handle_build_annotations(self._make_args())

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: failed to connect to Ollama" in captured.err
