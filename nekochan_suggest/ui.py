"""Streamlit GUI モジュール。

nekochan-suggest-ui コマンドのエントリーポイントを提供する。
streamlit が未インストールの場合は ImportError が発生する。
インストール方法: uv sync --extra gui
"""

from __future__ import annotations

import streamlit as st  # type: ignore[import-untyped]


def main() -> None:
    """GUI エントリーポイント。Streamlit アプリを起動する。

    Note:
        ビジネスロジックは別フィーチャー（001-nekochan-suggest）で実装予定。
    """
    st.write("未実装（別フィーチャー 001-nekochan-suggest で実装予定）")


if __name__ == "__main__":
    main()
