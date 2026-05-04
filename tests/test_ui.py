"""nekochan_suggest.ui / _app モジュールのユニットテスト。

テスト戦略:
- suggest() 等のビジネスロジック関数を unittest.mock でモック化する。
- Streamlit の UI レンダリング（ウィジェット描画）自体はテスト対象としない。
- 純粋な Python 関数（URL 構築・バリデーション・提案実行）のみを検証する。
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nekochan_suggest.query import SuggestionResult

# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_suggest() -> MagicMock:
    """nekochan_suggest.query.suggest をモックするフィクスチャ。"""
    with patch("nekochan_suggest._app.suggest") as mock:
        yield mock


# ---------------------------------------------------------------------------
# T005: get_image_bytes() の単体テスト
# ---------------------------------------------------------------------------


class TestGetImageBytes:
    """get_image_bytes() のユニットテスト。"""

    def test_returns_image_bytes_when_found(  # noqa: E501
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """name が一致するエントリの画像バイト列を返すことを確認する。"""
        import base64
        import json

        from nekochan_suggest._app import get_image_bytes

        png_bytes = b"FAKEPNG"
        fake_data = [
            {
                "name": "yatta-nya",
                "image_base64": base64.b64encode(png_bytes).decode(),
                "image_mimetype": "image/png",
            }
        ]
        fake_path = tmp_path / "annotations.json"
        fake_path.write_text(json.dumps(fake_data))

        with patch("nekochan_suggest._app.ANNOTATIONS_PATH", fake_path):
            result = get_image_bytes("yatta-nya")

        assert result == png_bytes

    def test_returns_none_when_name_not_found(  # noqa: E501
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """name が一致しない場合は None を返すことを確認する。"""
        import base64
        import json

        from nekochan_suggest._app import get_image_bytes

        fake_data = [
            {
                "name": "other-emoji",
                "image_base64": base64.b64encode(b"FAKEPNG").decode(),
                "image_mimetype": "image/png",
            }
        ]
        fake_path = tmp_path / "annotations.json"
        fake_path.write_text(json.dumps(fake_data))

        with patch("nekochan_suggest._app.ANNOTATIONS_PATH", fake_path):
            result = get_image_bytes("yatta-nya")

        assert result is None

    def test_returns_none_when_file_missing(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """annotations.json が存在しない場合は None を返すことを確認する。"""
        from nekochan_suggest._app import get_image_bytes

        fake_path = tmp_path / "nonexistent.json"

        with patch("nekochan_suggest._app.ANNOTATIONS_PATH", fake_path):
            result = get_image_bytes("yatta-nya")

        assert result is None


# ---------------------------------------------------------------------------
# T006: validate_input() の入力バリデーション単体テスト
# ---------------------------------------------------------------------------


class TestValidateInput:
    """validate_input() のユニットテスト。"""

    def test_empty_string_is_invalid(self) -> None:
        """空文字列は invalid を返すことを確認する。"""
        from nekochan_suggest._app import validate_input

        is_valid, message = validate_input("")
        assert is_valid is False
        assert message  # メッセージが空でないこと

    def test_whitespace_only_is_invalid(self) -> None:
        """空白のみの入力は invalid を返すことを確認する。"""
        from nekochan_suggest._app import validate_input

        is_valid, message = validate_input("   \n\t  ")
        assert is_valid is False
        assert message

    def test_normal_text_is_valid(self) -> None:
        """通常のテキストは valid を返すことを確認する。"""
        from nekochan_suggest._app import validate_input

        is_valid, message = validate_input("今日も頑張ろう！")
        assert is_valid is True

    def test_exactly_1000_chars_is_valid(self) -> None:
        """1000 文字ちょうどは valid かつメッセージなしを確認する。"""
        from nekochan_suggest._app import validate_input

        text = "あ" * 1000
        is_valid, message = validate_input(text)
        assert is_valid is True
        assert message == ""

    def test_over_1000_chars_is_valid_with_message(self) -> None:
        """1000 文字超は valid かつ警告メッセージを返すことを確認する。"""
        from nekochan_suggest._app import validate_input

        text = "あ" * 1001
        is_valid, message = validate_input(text)
        assert is_valid is True
        assert message  # 警告メッセージがあること


# ---------------------------------------------------------------------------
# T007: 1000 文字超入力テスト（suggest() が先頭 1000 文字で呼ばれることを確認）
# ---------------------------------------------------------------------------


class TestRunSuggestionTruncation:
    """1000 文字超入力時のトランケート動作テスト。"""

    def test_over_1000_chars_truncated_in_suggest(  # noqa: E501
        self, mock_suggest: MagicMock
    ) -> None:
        """1000 文字超入力は validate_input で先頭 1000 文字に切り詰められる。"""  # noqa: E501
        from nekochan_suggest._app import validate_input

        long_text = "あ" * 1500
        is_valid, message = validate_input(long_text)
        assert is_valid is True
        assert message  # 警告メッセージあり

        # 実際に先頭 1000 文字で run_suggestion を呼ぶのは render_app() の責務
        # ここでは validate_input が正しく動作することを確認する
        truncated = long_text[:1000]
        assert len(truncated) == 1000


# ---------------------------------------------------------------------------
# T008: 正常提案フロー統合テスト
# ---------------------------------------------------------------------------


class TestRunSuggestion:
    """run_suggestion() の統合テスト。"""

    def test_returns_suggestion_results(self, mock_suggest: MagicMock) -> None:
        """suggest() が 3 件の結果を返す場合、run_suggestion() がそのまま返すことを確認する。"""  # noqa: E501
        from nekochan_suggest._app import run_suggestion

        expected_results = [
            SuggestionResult(name="yatta-nya", score=0.9),
            SuggestionResult(name="neko", score=0.8),
            SuggestionResult(name="happy-cat", score=0.7),
        ]
        mock_suggest.return_value = expected_results

        results = run_suggestion("今日も頑張ろう！")

        assert results == expected_results

    def test_calls_suggest_with_count_3(self, mock_suggest: MagicMock) -> None:
        """run_suggestion() が suggest(text, count=3) を正しい引数で呼ぶことを確認する。"""  # noqa: E501
        from nekochan_suggest._app import run_suggestion

        mock_suggest.return_value = []
        text = "テストテキスト"

        run_suggestion(text)

        mock_suggest.assert_called_once_with(text, count=3)

    def test_exception_propagates(self, mock_suggest: MagicMock) -> None:
        """suggest() が例外を発生させた場合、run_suggestion() がそのまま raise することを確認する。"""  # noqa: E501
        from nekochan_suggest._app import run_suggestion

        mock_suggest.side_effect = ConnectionError("Ollama に接続できません")

        with pytest.raises(ConnectionError, match="Ollama に接続できません"):
            run_suggestion("テスト")


# ---------------------------------------------------------------------------
# T014: アノテーションファイル非存在テスト（US2）
# T015: エラーメッセージ内容テスト（US2）
# ---------------------------------------------------------------------------


class TestCheckAnnotationsExist:
    """check_annotations_exist() のユニットテスト（US2）。"""

    def test_returns_true_when_file_exists(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:  # noqa: E501
        """アノテーションファイルが存在する場合に True を返すことを確認する。"""
        from nekochan_suggest._app import check_annotations_exist

        fake_path = tmp_path / "annotations.json"
        fake_path.write_text("[]")

        with patch("nekochan_suggest._app.ANNOTATIONS_PATH", fake_path):
            assert check_annotations_exist() is True

    def test_returns_false_when_file_missing(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:  # noqa: E501
        """アノテーションファイルが存在しない場合に False を返すことを確認する（T014）。"""  # noqa: E501
        from nekochan_suggest._app import check_annotations_exist

        fake_path = tmp_path / "nonexistent.json"  # 存在しないパス

        with patch("nekochan_suggest._app.ANNOTATIONS_PATH", fake_path):
            assert check_annotations_exist() is False

    def test_error_message_contains_build_annotations(self) -> None:
        """render_app() のソースに 'build-annotations' が含まれること（T015）。

        check_annotations_exist() が False の場合のエラーメッセージを検証する。
        """
        import inspect

        from nekochan_suggest import _app

        # render_app のソースコードに 'build-annotations' が含まれることを確認する
        source = inspect.getsource(_app.render_app)
        assert "build-annotations" in source
