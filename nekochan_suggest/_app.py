"""Streamlit アプリ本体モジュール。

nekochan-suggest-ui コマンドによって起動される Streamlit アプリ。
UI 表示処理のみを担い、ビジネスロジックは query.suggest() に委譲する。

起動方法:
    nekochan-suggest-ui  # ui.py の main() 経由で起動
"""

from __future__ import annotations

import base64
import json

import streamlit as st  # type: ignore[import-untyped]

from nekochan_suggest.query import ANNOTATIONS_PATH, SuggestionResult, suggest

# テキスト入力の最大文字数
_MAX_INPUT_LENGTH = 1000


def get_image_bytes(name: str) -> tuple[bytes, str] | None:
    """annotations.json から name に対応する画像バイト列と MIME タイプを返す。

    Args:
        name: 絵文字ファイル名（拡張子なし、例: "yatta-nya"）。

    Returns:
        (画像バイト列, MIME タイプ) のタプル。
        ファイルが存在しないか該当名が見つからない場合は None。
    """
    if not ANNOTATIONS_PATH.exists():
        return None
    with ANNOTATIONS_PATH.open(encoding="utf-8") as f:
        records: list[dict[str, object]] = json.load(f)
    for record in records:
        if record.get("name") == name:
            b64 = record.get("image_base64")
            mimetype = record.get("image_mimetype", "image/png")
            if isinstance(b64, str) and b64:
                return base64.b64decode(b64), str(mimetype)
    return None


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
        return False, "Please enter some text."
    if len(text) > _MAX_INPUT_LENGTH:
        return True, (
            f"Input exceeds {_MAX_INPUT_LENGTH} characters. "
            f"Only the first {_MAX_INPUT_LENGTH} characters will be used."
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
    st.title("Nekochan Emoji Suggestions")

    # アノテーションファイル存在チェック（US2）
    if not check_annotations_exist():
        st.error(
            "Annotation file not found.\n\n"
            "Please run the following command to build annotations:\n\n"
            "```\nnekochan-suggest build-annotations\n```"
        )
        st.stop()
        return

    # テキスト入力欄
    text = st.text_area("Enter text to get emoji suggestions", height=120)

    if st.button("Suggest"):
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
            st.error(f"Error during suggestion: {e}")
            return

        # 結果表示（縦方向カードレイアウト）
        if not results:
            st.info("No suggestions found.")
            return

        for result in results:
            image_result = get_image_bytes(result.name)
            if image_result is not None:
                image_bytes, mimetype = image_result
                if mimetype == "image/gif":
                    # GIF は st.image() だと最初のフレームしか表示されないため
                    # HTML img タグでアニメーションとして埋め込む
                    b64_str = base64.b64encode(image_bytes).decode()
                    st.markdown(
                        f'<img src="data:image/gif;base64,{b64_str}" width="64">',
                        unsafe_allow_html=True,
                    )
                else:
                    st.image(image_bytes, width=64)
            st.write(f"**{result.name}** — score: {result.score:.3f}")
            st.markdown("---")


if __name__ == "__main__":  # pragma: no cover
    render_app()
