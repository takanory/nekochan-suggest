"""アノテーション生成・ストレージ機能のテスト。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nekochan_suggest.annotations import (
    build_all_annotations,
    fetch_aliases,
    fetch_emoji_data,
    generate_annotation,
    generate_embedding,
    gif_first_frame_as_png_base64,
    gif_frames_as_png_base64_list,
    load_existing_annotations,
    save_annotations_file,
)

# ---------------------------------------------------------------------------
# T003: fetch_aliases() テスト
# ---------------------------------------------------------------------------


class TestFetchAliases:
    """fetch_aliases() の単体テスト。"""

    def test_returns_dict_on_success(self) -> None:
        """正常系: HTTP 200 のとき aliases dict を返す。"""
        payload = json.dumps(
            {"yatta-nya": ["yatta"], "niko-nya": ["niko", "smile"]}
        ).encode()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = payload
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = fetch_aliases("http://example.com/aliases.json", timeout=10)

        assert result == {"yatta-nya": ["yatta"], "niko-nya": ["niko", "smile"]}

    def test_propagates_oserror(self) -> None:
        """接続エラー（OSError）は ValueError に変換せずそのまま伝播する。"""
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            with pytest.raises(OSError):
                fetch_aliases("http://example.com/aliases.json", timeout=10)

    def test_raises_value_error_on_non_200(self) -> None:
        """HTTP 非200 ステータスは ValueError を送出する。"""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(ValueError, match="HTTP 404"):
                fetch_aliases("http://example.com/aliases.json", timeout=10)


# ---------------------------------------------------------------------------
# fetch_emoji_data() テスト
# ---------------------------------------------------------------------------


class TestFetchEmojiData:
    """fetch_emoji_data() の単体テスト。"""

    def test_returns_dict_on_success(self) -> None:
        """正常系: HTTP 200 のとき emoji dict を返す。"""
        payload = json.dumps(
            {
                "yatta-nya": {
                    "aliases": ["yatta"],
                    "base64": "R0l=",
                    "mimetype": "image/gif",
                },
            }
        ).encode()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = payload
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = fetch_emoji_data(
                "http://example.com/nekochan_emoji.json", timeout=10
            )

        assert result == {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }

    def test_propagates_oserror(self) -> None:
        """接続エラー（OSError）はそのまま伝播する。"""
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            with pytest.raises(OSError):
                fetch_emoji_data("http://example.com/nekochan_emoji.json", timeout=10)

    def test_raises_value_error_on_non_200(self) -> None:
        """HTTP 非200 ステータスは ValueError を送出する。"""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(ValueError, match="HTTP 404"):
                fetch_emoji_data("http://example.com/nekochan_emoji.json", timeout=10)


# ---------------------------------------------------------------------------
# T004: generate_annotation() テスト
# ---------------------------------------------------------------------------


class TestGenerateAnnotation:
    """generate_annotation() の単体テスト。"""

    def _make_ollama_response(self, response_text: str) -> MagicMock:
        """Ollama API 正常レスポンスのモックを返す。"""
        payload = json.dumps({"response": response_text}).encode()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = payload
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    def test_returns_str_on_success(self) -> None:
        """正常系: Ollama response フィールドを str で返す。"""
        with patch(
            "urllib.request.urlopen",
            return_value=self._make_ollama_response("A joyful cat."),
        ):
            result = generate_annotation(
                emoji_name="yatta-nya",
                aliases=["yatta"],
                ollama_url="http://localhost:11434",
                llm_model="qwen3.5",
                timeout=30,
            )
        assert result == "A joyful cat."

    def test_sends_images_when_image_base64_given(self) -> None:
        """images リストを指定したとき、Ollama リクエストに images フィールドが含まれる。"""
        captured_body: list[dict] = []

        def fake_urlopen(req, timeout):  # noqa: ANN001
            captured_body.append(json.loads(req.data))
            return self._make_ollama_response("A cat emoji.")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            generate_annotation(
                emoji_name="yatta-nya",
                aliases=["yatta"],
                ollama_url="http://localhost:11434",
                llm_model="qwen3.5",
                timeout=30,
                images=["R0l="],
            )

        assert captured_body[0]["images"] == ["R0l="]

    def test_no_images_field_when_image_base64_empty(self) -> None:
        """images が None のとき、Ollama リクエストに images フィールドが含まれない。"""
        captured_body: list[dict] = []

        def fake_urlopen(req, timeout):  # noqa: ANN001
            captured_body.append(json.loads(req.data))
            return self._make_ollama_response("A cat emoji.")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            generate_annotation(
                emoji_name="yatta-nya",
                aliases=["yatta"],
                ollama_url="http://localhost:11434",
                llm_model="qwen3.5",
                timeout=30,
                images=None,
            )

        assert "images" not in captured_body[0]

    def test_multiple_images_sent_in_list(self) -> None:
        """images に複数フレームを渡すと Ollama に複数画像リストとして送信される。"""
        captured_body: list[dict] = []

        def fake_urlopen(req, timeout):  # noqa: ANN001
            captured_body.append(json.loads(req.data))
            return self._make_ollama_response("A cat animation.")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            generate_annotation(
                emoji_name="yatta-nya",
                aliases=["yatta"],
                ollama_url="http://localhost:11434",
                llm_model="qwen3.5",
                timeout=30,
                images=["frame1", "frame2", "frame3"],
            )

        assert captured_body[0]["images"] == ["frame1", "frame2", "frame3"]

    def test_gif_frame_count_included_in_prompt(self) -> None:
        """gif_frame_count > 1 のとき、プロンプトにアニメーション旨が含まれる。"""
        captured_body: list[dict] = []

        def fake_urlopen(req, timeout):  # noqa: ANN001
            captured_body.append(json.loads(req.data))
            return self._make_ollama_response("A cat animation.")

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            generate_annotation(
                emoji_name="yatta-nya",
                aliases=[],
                ollama_url="http://localhost:11434",
                llm_model="qwen3.5",
                timeout=30,
                images=["f1", "f2"],
                gif_frame_count=2,
            )

        assert (
            "These are 2 frames from an animated GIF emoji."
            in captured_body[0]["prompt"]
        )

    def test_propagates_timeout_error(self) -> None:
        """タイムアウト（TimeoutError）は伝播する。"""
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            with pytest.raises(TimeoutError):
                generate_annotation(
                    emoji_name="yatta-nya",
                    aliases=[],
                    ollama_url="http://localhost:11434",
                    llm_model="qwen3.5",
                    timeout=1,
                )

    def test_propagates_oserror(self) -> None:
        """接続失敗（OSError）は伝播する。"""
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            with pytest.raises(OSError):
                generate_annotation(
                    emoji_name="yatta-nya",
                    aliases=[],
                    ollama_url="http://localhost:11434",
                    llm_model="qwen3.5",
                    timeout=30,
                )


# ---------------------------------------------------------------------------
# T005: generate_embedding() テスト
# ---------------------------------------------------------------------------


class TestGenerateEmbedding:
    """generate_embedding() の単体テスト。"""

    def test_returns_list_of_float(self) -> None:
        """正常系: list[float] を返す。"""
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])

        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model
        ):
            result = generate_embedding(
                "A joyful cat.", embed_model="intfloat/multilingual-e5-base"
            )

        assert result == [0.1, 0.2, 0.3]

    def test_encode_receives_passage_prefix(self) -> None:
        """encode() の引数に 'passage: ' プレフィックスが付与される。"""
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1])

        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model
        ):
            generate_embedding(
                "A joyful cat.", embed_model="intfloat/multilingual-e5-base"
            )

        mock_model.encode.assert_called_once_with("passage: A joyful cat.")


# ---------------------------------------------------------------------------
# T006: build_all_annotations() 結合テスト
# ---------------------------------------------------------------------------

_SAMPLE_ALIASES = {
    "yatta-nya": ["yatta"],
    "nemui-nya": ["nemui", "sleepy"],
    "niko-nya": ["niko", "smile"],
    "hare-nya": ["hare", "sunny"],
}
_SAMPLE_EMOJI_DATA = {
    "yatta-nya": {"aliases": ["yatta"], "base64": "iVBO=", "mimetype": "image/png"},
    "nemui-nya": {
        "aliases": ["nemui", "sleepy"],
        "base64": "iVBO=",
        "mimetype": "image/png",
    },
    "niko-nya": {
        "aliases": ["niko", "smile"],
        "base64": "iVBO=",
        "mimetype": "image/png",
    },
    "hare-nya": {
        "aliases": ["hare", "sunny"],
        "base64": "iVBO=",
        "mimetype": "image/png",
    },
}
_SAMPLE_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "llm_model": "qwen3.5",
    "embed_model": "intfloat/multilingual-e5-base",
    "timeout": "30",
}


@pytest.fixture()
def mock_deps() -> dict:
    """build_all_annotations 依存関数をすべてモックするフィクスチャ。"""
    with (
        patch("nekochan_suggest.annotations.fetch_aliases") as m_fetch,
        patch("nekochan_suggest.annotations.fetch_emoji_data") as m_fetch_emoji,
        patch("nekochan_suggest.annotations.generate_annotation") as m_gen,
        patch("nekochan_suggest.annotations.generate_embedding") as m_emb,
        patch("nekochan_suggest.annotations.load_existing_annotations") as m_load,
        patch("nekochan_suggest.annotations.save_annotations_file") as m_save,
    ):
        m_fetch.return_value = _SAMPLE_ALIASES
        m_fetch_emoji.return_value = _SAMPLE_EMOJI_DATA
        m_gen.return_value = "A cat annotation."
        m_emb.return_value = [0.1, 0.2, 0.3]
        m_load.return_value = []
        yield {
            "fetch": m_fetch,
            "fetch_emoji": m_fetch_emoji,
            "gen": m_gen,
            "emb": m_emb,
            "load": m_load,
            "save": m_save,
        }


class TestBuildAllAnnotations:
    """build_all_annotations() の結合テスト。"""

    def test_dry_run_prints_first_3_to_stdout(
        self, mock_deps: dict, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """ドライラン: stdout に先頭 3 件の JSON プレビューが出力される。"""
        build_all_annotations(dry_run=True, config=_SAMPLE_CONFIG)

        captured = capsys.readouterr()
        lines = [line for line in captured.out.splitlines() if line.strip()]
        assert len(lines) == 3
        for line in lines:
            record = json.loads(line)
            assert "name" in record
            assert "annotation" in record
            assert "embedding" in record
            assert "image_base64" in record
            assert "image_mimetype" in record

    def test_dry_run_does_not_call_save(self, mock_deps: dict) -> None:
        """ドライラン: save_annotations_file が呼ばれない。"""
        build_all_annotations(dry_run=True, config=_SAMPLE_CONFIG)
        mock_deps["save"].assert_not_called()

    def test_normal_run_calls_save_per_record(self, mock_deps: dict) -> None:
        """通常実行: 各レコード処理後に save_annotations_file が呼ばれる。"""
        build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)
        assert mock_deps["save"].call_count == len(_SAMPLE_ALIASES)

    def test_resume_skips_existing_names(self, mock_deps: dict) -> None:
        """再開: load_existing_annotations に既存名が含まれる場合スキップする。"""
        mock_deps["load"].return_value = [
            {"name": "yatta-nya", "annotation": "existing", "embedding": [0.1]}
        ]
        build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)
        # yatta-nya はスキップされ、残り 3 件のみ save される
        assert mock_deps["save"].call_count == len(_SAMPLE_ALIASES) - 1

    def test_skips_and_reports_on_llm_error(
        self, mock_deps: dict, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """1件 LLM エラー: スキップして残りを処理し、完了後にスキップ一覧を stderr に出力。"""
        call_count = 0

        def flaky_gen(*args, **kwargs) -> str:  # noqa: ANN002
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("Ollama connection refused")
            return "A cat annotation."

        mock_deps["gen"].side_effect = flaky_gen
        build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        captured = capsys.readouterr()
        assert "Skipped" in captured.err
        # 残り 3 件は正常処理
        assert mock_deps["save"].call_count == len(_SAMPLE_ALIASES) - 1

    def test_progress_displayed_to_stderr(
        self, mock_deps: dict, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """進行表示: [N/total] 絵文字名 形式が stderr に出力される。"""
        build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        captured = capsys.readouterr()
        assert "[1/" in captured.err

    def test_fetch_oserror_raised_as_value_error(self, mock_deps: dict) -> None:
        """aliases フェッチ OSError は ValueError として伝播する。"""
        mock_deps["fetch"].side_effect = OSError("network error")
        with pytest.raises(ValueError, match="failed to fetch aliases.json"):
            build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

    def test_fetch_emoji_oserror_raised_as_value_error(self, mock_deps: dict) -> None:
        """emoji フェッチ OSError は ValueError として伝播する。"""
        mock_deps["fetch_emoji"].side_effect = OSError("network error")
        with pytest.raises(ValueError, match="failed to fetch nekochan_emoji.json"):
            build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

    def test_missing_emoji_data_uses_empty_strings(self, mock_deps: dict) -> None:
        """絵文字名が nekochan_emoji.json にない場合、image_base64/mimetype は空文字列。"""
        mock_deps["fetch_emoji"].return_value = {}  # 空の emoji データ
        build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        # 保存されたレコードの画像データが空文字列であることを確認
        first_call_records = mock_deps["save"].call_args_list[0][0][0]
        last_record = first_call_records[-1]
        assert last_record["image_base64"] == ""
        assert last_record["image_mimetype"] == ""

    def test_gif_image_passed_to_llm(self, mock_deps: dict) -> None:
        """GIF 画像の絵文字は複数フレームに変換されて LLM に渡される。"""
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
            "nemui-nya": {
                "aliases": ["nemui"],
                "base64": "iVBO=",
                "mimetype": "image/png",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["PNG_F1", "PNG_F2"],
        ) as mock_frames:
            build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        # GIF フレーム抽出が呼ばれたことを確認
        mock_frames.assert_called_once_with("R0l=", 4)
        called_names = [c.args[0] for c in mock_deps["gen"].call_args_list]
        assert "yatta-nya" in called_names
        assert "nemui-nya" in called_names

    def test_gif_image_base64_saved_in_record(self, mock_deps: dict) -> None:
        """GIF 画像の image_base64 がレコードに元の GIF base64 で保存される。"""
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["PNG_F1"],
        ):
            build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        saved_records = mock_deps["save"].call_args[0][0]
        record = next(r for r in saved_records if r["name"] == "yatta-nya")
        # 保存されるのは元の GIF base64（変換前）
        assert record["image_base64"] == "R0l="
        assert record["image_mimetype"] == "image/gif"

    def test_gif_existing_entry_is_regenerated(self, mock_deps: dict) -> None:
        """既存 GIF エントリはスキップされず再生成される（FR-012）。"""
        mock_deps["load"].return_value = [
            {
                "name": "yatta-nya",
                "annotation": "old",
                "embedding": [0.1],
                "image_mimetype": "image/gif",
            }
        ]
        mock_deps["fetch"].return_value = {"yatta-nya": ["yatta"]}
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["PNG_F1"],
        ):
            build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        # GIF 既存エントリは再生成される（save が呼ばれる）
        assert mock_deps["gen"].call_count == 1

    def test_png_image_passed_as_single_image_list(self, mock_deps: dict) -> None:
        """PNG 画像は単一要素の images リストとして LLM に渡される。"""
        captured_calls: list[dict] = []

        def capture_gen(*args, **kwargs):  # noqa: ANN002
            captured_calls.append({"args": args, "kwargs": kwargs})
            return "annotation"

        mock_deps["gen"].side_effect = capture_gen
        mock_deps["fetch"].return_value = {"niko-nya": ["niko"]}
        mock_deps["fetch_emoji"].return_value = {
            "niko-nya": {
                "aliases": ["niko"],
                "base64": "iVBO=",
                "mimetype": "image/png",
            },
        }
        build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        assert len(captured_calls) == 1
        assert captured_calls[0]["kwargs"].get("images") == ["iVBO="]

    def test_debug_log_extracted_frames(
        self, mock_deps: dict, caplog: pytest.LogCaptureFixture
    ) -> None:
        """GIF 処理時に DEBUG ログでフレーム数が記録される（NF-001）。"""
        import logging

        mock_deps["fetch"].return_value = {"yatta-nya": ["yatta"]}
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["F1", "F2", "F3"],
        ):
            with caplog.at_level(logging.DEBUG, logger="nekochan_suggest.annotations"):
                build_all_annotations(dry_run=False, config=_SAMPLE_CONFIG)

        assert any(
            "Extracted 3 frames" in r.message and "yatta-nya" in r.message
            for r in caplog.records
        )

    def test_gif_max_frames_zero_uses_default(self, mock_deps: dict) -> None:
        """gif_max_frames=0 のとき WARNING を出してデフォルト 4 を使用する（EC-003）。"""
        config = {**_SAMPLE_CONFIG, "gif_max_frames": "0"}
        mock_deps["fetch"].return_value = {"yatta-nya": ["yatta"]}
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["F1"],
        ) as mock_frames:
            build_all_annotations(dry_run=False, config=config)
        # デフォルト 4 が渡される
        mock_frames.assert_called_once_with("R0l=", 4)

    def test_gif_max_frames_negative_uses_default(self, mock_deps: dict) -> None:
        """gif_max_frames=-1 のとき WARNING を出してデフォルト 4 を使用する（EC-003）。"""
        config = {**_SAMPLE_CONFIG, "gif_max_frames": "-1"}
        mock_deps["fetch"].return_value = {"yatta-nya": ["yatta"]}
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["F1"],
        ) as mock_frames:
            build_all_annotations(dry_run=False, config=config)
        mock_frames.assert_called_once_with("R0l=", 4)

    def test_gif_max_frames_non_integer_uses_default(self, mock_deps: dict) -> None:
        """gif_max_frames='abc' のとき WARNING を出してデフォルト 4 を使用する（EC-003）。"""
        config = {**_SAMPLE_CONFIG, "gif_max_frames": "abc"}
        mock_deps["fetch"].return_value = {"yatta-nya": ["yatta"]}
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["F1"],
        ) as mock_frames:
            build_all_annotations(dry_run=False, config=config)
        mock_frames.assert_called_once_with("R0l=", 4)

    def test_gif_max_frames_two_is_passed_to_extractor(self, mock_deps: dict) -> None:
        """gif_max_frames='2' のとき gif_frames_as_png_base64_list に max_frames=2 が渡される。"""
        config = {**_SAMPLE_CONFIG, "gif_max_frames": "2"}
        mock_deps["fetch"].return_value = {"yatta-nya": ["yatta"]}
        mock_deps["fetch_emoji"].return_value = {
            "yatta-nya": {
                "aliases": ["yatta"],
                "base64": "R0l=",
                "mimetype": "image/gif",
            },
        }
        with patch(
            "nekochan_suggest.annotations.gif_frames_as_png_base64_list",
            return_value=["F1", "F2"],
        ) as mock_frames:
            build_all_annotations(dry_run=False, config=config)
        mock_frames.assert_called_once_with("R0l=", 2)


# ---------------------------------------------------------------------------
# TestBuildAnnotationPromptWithGifFrameCount — T003
# ---------------------------------------------------------------------------


class TestBuildAnnotationPromptWithGifFrameCount:
    """_build_annotation_prompt() の gif_frame_count パラメータのテスト。"""

    def _call(
        self, emoji_name: str, aliases: list[str], gif_frame_count: int = 0
    ) -> str:
        from nekochan_suggest.annotations import _build_annotation_prompt

        return _build_annotation_prompt(
            emoji_name, aliases, gif_frame_count=gif_frame_count
        )

    def test_no_prefix_when_frame_count_zero(self) -> None:
        """gif_frame_count=0 のとき、アニメーションプレフィックスなし。"""
        result = self._call("yatta-nya", [], gif_frame_count=0)
        assert "frames from an animated GIF" not in result

    def test_no_prefix_when_frame_count_one(self) -> None:
        """gif_frame_count=1 のとき、アニメーションプレフィックスなし。"""
        result = self._call("yatta-nya", [], gif_frame_count=1)
        assert "frames from an animated GIF" not in result

    def test_prefix_added_when_frame_count_four(self) -> None:
        """gif_frame_count=4 のとき、プロンプト先頭に 'These are 4 frames...' が追記される。"""
        result = self._call("yatta-nya", [], gif_frame_count=4)
        assert result.startswith("These are 4 frames from an animated GIF emoji.")

    def test_prefix_frame_count_is_dynamic(self) -> None:
        """gif_frame_count が動的にプロンプトに反映される。"""
        result = self._call("yatta-nya", [], gif_frame_count=2)
        assert "These are 2 frames from an animated GIF emoji." in result


# ---------------------------------------------------------------------------
# TestGifFramesAsPngBase64List — T002
# ---------------------------------------------------------------------------


class TestGifFramesAsPngBase64List:
    """gif_frames_as_png_base64_list() の単体テスト。"""

    def _make_animated_gif_base64(self, n_frames: int = 4) -> str:
        """n_frames フレームのアニメーション GIF を base64 で返す。"""
        import base64 as b64mod
        import io as io_mod

        from PIL import Image

        frames = [
            Image.new("RGBA", (2, 2), (i * 60 % 255, 0, 0, 255))
            for i in range(n_frames)
        ]
        buf = io_mod.BytesIO()
        frames[0].save(
            buf,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            loop=0,
        )
        return b64mod.b64encode(buf.getvalue()).decode()

    def _make_single_frame_gif_base64(self) -> str:
        """1フレームの GIF を base64 で返す。"""
        return self._make_animated_gif_base64(n_frames=1)

    def test_returns_list_of_strings(self) -> None:
        """戻り値が list[str] であること。"""
        gif_b64 = self._make_animated_gif_base64(4)
        result = gif_frames_as_png_base64_list(gif_b64, max_frames=4)
        assert isinstance(result, list)
        assert all(isinstance(f, str) for f in result)

    def test_returns_png_frames(self) -> None:
        """返却フレームが PNG base64 であること。"""
        import base64 as b64mod
        import io as io_mod

        from PIL import Image

        gif_b64 = self._make_animated_gif_base64(2)
        result = gif_frames_as_png_base64_list(gif_b64, max_frames=2)
        for frame_b64 in result:
            img = Image.open(io_mod.BytesIO(b64mod.b64decode(frame_b64)))
            assert img.format == "PNG"

    def test_single_frame_gif_returns_one_frame(self) -> None:
        """1フレーム GIF は max_frames に関係なく 1 フレームを返す。"""
        gif_b64 = self._make_single_frame_gif_base64()
        result = gif_frames_as_png_base64_list(gif_b64, max_frames=4)
        assert len(result) == 1

    def test_total_frames_less_than_max_returns_all(self) -> None:
        """GIF のフレーム数が max_frames 未満の場合、全フレームを返す（FR-006）。"""
        gif_b64 = self._make_animated_gif_base64(n_frames=3)
        result = gif_frames_as_png_base64_list(gif_b64, max_frames=10)
        assert len(result) == 3

    def test_even_sampling_10frames_max4(self) -> None:
        """10フレーム / max=4 のとき均等間隔で 4 フレームを返す（FR-007）。

        期待インデックス: i * (10-1) // (4-1) → 0, 3, 6, 9
        """
        gif_b64 = self._make_animated_gif_base64(n_frames=10)
        result = gif_frames_as_png_base64_list(gif_b64, max_frames=4)
        assert len(result) == 4

    def test_max_frames_one_returns_first_frame(self) -> None:
        """max_frames=1 のとき最初のフレームのみ返す（N=1 特殊ケース）。"""
        gif_b64 = self._make_animated_gif_base64(n_frames=5)
        result = gif_frames_as_png_base64_list(gif_b64, max_frames=1)
        assert len(result) == 1

    def test_corrupt_gif_raises_exception(self) -> None:
        """壊れた GIF バイト列（無効データ）を渡すと Exception が送出される（FR-010, EC-002）。"""
        import base64 as b64mod

        corrupt_b64 = b64mod.b64encode(b"not a gif").decode()
        with pytest.raises(Exception):  # noqa: B017
            gif_frames_as_png_base64_list(corrupt_b64, max_frames=4)


# ---------------------------------------------------------------------------
# gif_first_frame_as_png_base64() 単体テスト
# ---------------------------------------------------------------------------


class TestGifFirstFrameAsPngBase64:
    """gif_first_frame_as_png_base64() の単体テスト。"""

    def _make_gif_base64(self) -> str:
        """1x1 ピクセルの GIF を base64 で返す。"""
        import base64
        import io

        from PIL import Image

        buf = io.BytesIO()
        img = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
        img.save(buf, format="GIF")
        return base64.b64encode(buf.getvalue()).decode()

    def test_returns_png_base64(self) -> None:
        """GIF base64 を渡すと PNG base64 が返る。"""
        import base64
        import io

        from PIL import Image

        gif_b64 = self._make_gif_base64()
        result = gif_first_frame_as_png_base64(gif_b64)
        png_bytes = base64.b64decode(result)
        img = Image.open(io.BytesIO(png_bytes))
        assert img.format == "PNG"

    def test_output_is_string(self) -> None:
        """戻り値が str であることを確認する。"""
        gif_b64 = self._make_gif_base64()
        result = gif_first_frame_as_png_base64(gif_b64)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# save_annotations_file() 単体テスト（E1 対応）
# ---------------------------------------------------------------------------


class TestSaveAnnotationsFile:
    """save_annotations_file() の単体テスト。"""

    def test_creates_parent_dir(self, tmp_path: Path) -> None:
        """親ディレクトリが存在しない場合に自動作成する。"""
        target = tmp_path / "nested" / "dir" / "annotations.json"
        records = [{"name": "yatta-nya", "annotation": "joy", "embedding": [0.1]}]
        save_annotations_file(records, target)
        assert target.exists()

    def test_writes_valid_json(self, tmp_path: Path) -> None:
        """JSON として読み込める内容を書き込む。"""
        target = tmp_path / "annotations.json"
        records = [{"name": "yatta-nya", "annotation": "joy", "embedding": [0.1]}]
        save_annotations_file(records, target)
        with target.open(encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == records


# ---------------------------------------------------------------------------
# load_existing_annotations() 単体テスト
# ---------------------------------------------------------------------------


class TestLoadExistingAnnotations:
    """load_existing_annotations() の単体テスト。"""

    def test_returns_empty_list_when_file_not_found(self, tmp_path: Path) -> None:
        """ファイル不在のとき空リストを返す。"""
        result = load_existing_annotations(tmp_path / "nonexistent.json")
        assert result == []

    def test_returns_records_from_existing_file(self, tmp_path: Path) -> None:
        """既存ファイルからレコードを読み込む。"""
        records = [{"name": "yatta-nya", "annotation": "joy", "embedding": [0.1]}]
        target = tmp_path / "annotations.json"
        target.write_text(json.dumps(records), encoding="utf-8")
        result = load_existing_annotations(target)
        assert result == records
