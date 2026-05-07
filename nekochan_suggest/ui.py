"""Streamlit GUI エントリーポイントモジュール。

nekochan-suggest-ui コマンドのエントリーポイントを提供する。
アプリ本体は nekochan_suggest/_app.py に実装されており、
このモジュールは streamlit.web.cli.main_run 経由でそれを起動するのみ。

インストール方法: uv sync --extra gui
"""

from __future__ import annotations

from pathlib import Path

from streamlit.web.cli import main_run  # type: ignore[import-untyped]

# Streamlit アプリ本体スクリプトのパス
_APP_PATH = Path(__file__).parent / "_app.py"


def main() -> None:
    """GUI エントリーポイント。Streamlit アプリを起動する。

    streamlit.web.cli.main_run を使用して _app.py を Streamlit サーバーとして起動する。
    """
    main_run.main([str(_APP_PATH)], standalone_mode=False)


if __name__ == "__main__":
    main()
