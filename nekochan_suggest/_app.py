"""Streamlit アプリ本体モジュール。

nekochan-suggest-ui コマンドによって起動される Streamlit アプリ。
UI 表示処理のみを担い、ビジネスロジックは query.suggest() に委譲する。

起動方法:
    nekochan-suggest-ui  # ui.py の main() 経由で起動
"""

from __future__ import annotations

import streamlit as st  # type: ignore[import-untyped]

from nekochan_suggest.query import ANNOTATIONS_PATH, SuggestionResult, suggest

# 画像 URL のベースパス
_IMAGE_BASE_URL = (
    "https://raw.githubusercontent.com/takanory/sphinx-nekochan"
    "/main/sphinx_nekochan/images/{name}.png"
)

# テキスト入力の最大文字数
_MAX_INPUT_LENGTH = 1000


def build_image_url(name: str) -> str:
    """絵文字名から GitHub Raw URL を構築して返す。

    Args:
        name: 絵文字ファイル名（拡張子なし、例: "yatta-nya"）。

    Returns:
        画像の GitHub Raw URL。
    """
    return _IMAGE_BASE_URL.format(name=name)


def validate_input(text: str) -> tuple[bool, str]:
    """テキスト入力をバリデーションし、(valid, message) を返す。

    空文字列・空白のみの場合は invalid を返す。
    1000 文字超の場合は先頭 1000 文字に切り詰め valid を返す（警告メッセージ付き）。

    Args:
        text: ユーザーが入力したテキスト。

    Returns:
        (is_valid, message) のタプル。
        is_valid が False の場合は入力促しメッセージを含む。
        is_valid が True で message が空でない場合は警告メッセージを含む。
    """
    stripped = text.strip()
    if not stripped:
        return False, "文章を入力してください。"
    if len(text) > _MAX_INPUT_LENGTH:
        return True, (
            f"入力が {_MAX_INPUT_LENGTH} 文字を超えているため、"
            f"先頭 {_MAX_INPUT_LENGTH} 文字で提案します。"
        )
    return True, ""


def check_annotations_exist() -> bool:
    """アノテーションファイルが存在するか確認する。

    Returns:
        アノテーションファイルが存在する場合 True、存在しない場合 False。
    """
    return ANNOTATIONS_PATH.exists()


def run_suggestion(text: str) -> list[SuggestionResult]:
    """テキストに基づいてネコチャン絵文字の提案を実行する。

    Args:
        text: 提案を求めるテキスト（1〜1000 文字）。

    Returns:
        スコア降順の SuggestionResult リスト（最大 3 件）。

    Raises:
        Exception: suggest() が例外を発生させた場合、そのまま呼び出し元に raise する。
    """
    return suggest(text, count=3)


def render_app() -> None:  # pragma: no cover
    """Streamlit アプリのメイン描画関数。

    アノテーションファイルの存在チェック、テキスト入力、提案実行、
    結果の縦方向カード表示を行う。
    """
    st.title("ネコチャン絵文字提案")

    # アノテーションファイル存在チェック（US2）
    if not check_annotations_exist():
        st.error(
            "アノテーションファイルが見つかりません。\n\n"
            "以下のコマンドを実行してアノテーションを構築してください:\n\n"
            "```\nnekochan-suggest build-annotations\n```"
        )
        st.stop()
        return

    # テキスト入力欄
    text = st.text_area("提案する文章を入力してください", height=120)

    if st.button("提案する"):
        is_valid, message = validate_input(text)
        if not is_valid:
            st.warning(message)
            return

        # 1000 文字超の場合は警告メッセージを表示
        if message:
            st.info(message)
            text = text[:_MAX_INPUT_LENGTH]

        # 提案実行
        try:
            results = run_suggestion(text)
        except Exception as e:  # noqa: BLE001
            st.error(f"提案処理でエラーが発生しました: {e}")
            return

        # 結果表示（縦方向カードレイアウト）
        if not results:
            st.info("候補が見つかりませんでした。")
            return

        for result in results:
            url = build_image_url(result.name)
            st.image(url, width=64)
            st.write(f"**{result.name}** — スコア: {result.score:.3f}")
            st.markdown("---")


if __name__ == "__main__":  # pragma: no cover
    render_app()
