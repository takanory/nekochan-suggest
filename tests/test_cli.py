"""CLI エントリーポイントの基本動作テスト。"""

import subprocess
import sys


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
    assert "--timeout" in result.stdout, "--timeout オプションが表示されていない"


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


def test_cli_text_stub_response() -> None:
    """テキスト引数に対してプレースホルダーメッセージが返ることを確認する。"""
    result = subprocess.run(
        [sys.executable, "-m", "nekochan_suggest.cli", "テスト入力"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"終了コードが 0 でない: {result.stderr}"
    assert len(result.stdout.strip()) > 0, "出力が空"
