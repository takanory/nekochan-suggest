"""query モジュールの単体テスト。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from nekochan_suggest import query
from nekochan_suggest.query import SuggestionResult

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "annotations.json"


def test_cosine_similarity_same_vector_returns_one() -> None:
    """同一ベクトルのコサイン類似度は 1.0 を返す。"""
    score = query._cosine_similarity([1.0, 2.0], [1.0, 2.0])

    assert score == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vector_returns_zero() -> None:
    """直交ベクトルのコサイン類似度は 0.0 を返す。"""
    score = query._cosine_similarity([1.0, 0.0], [0.0, 1.0])

    assert score == pytest.approx(0.0)


def test_cosine_similarity_zero_vector_guard_returns_zero() -> None:
    """ゼロベクトルを含む場合は 0.0 を返す。"""
    score = query._cosine_similarity([0.0, 0.0], [1.0, 2.0])

    assert score == pytest.approx(0.0)


def test_cosine_similarity_known_dot_product() -> None:
    """既知のドット積から期待値どおりのスコアを返す。"""
    score = query._cosine_similarity([1.0, 1.0], [1.0, 0.0])

    assert score == pytest.approx(2**-0.5)


def test_load_annotations_reads_fixture() -> None:
    """フィクスチャ JSON を正常に読み込める。"""
    records = query._load_annotations(FIXTURE_PATH)

    assert len(records) == 6
    assert records[0]["name"] == "yatta-nya"


def test_load_annotations_raises_when_file_missing(tmp_path: Path) -> None:
    """ファイル不在時は FileNotFoundError を送出する。"""
    with pytest.raises(FileNotFoundError):
        query._load_annotations(tmp_path / "missing.json")


def test_load_annotations_skips_missing_embedding() -> None:
    """embedding 欠損レコードを読み飛ばす。"""
    records = query._load_annotations(FIXTURE_PATH)

    names = {record["name"] for record in records}
    assert "mystery-nya" not in names


def test_load_annotations_skips_empty_embedding() -> None:
    """空 embedding レコードを読み飛ばす。"""
    records = query._load_annotations(FIXTURE_PATH)

    names = {record["name"] for record in records}
    assert "empty-nya" not in names


@patch("sentence_transformers.SentenceTransformer")
def test_embed_text_returns_float_list(mock_transformer: Mock) -> None:
    """encode 結果を list[float] に変換して返す。"""
    model = mock_transformer.return_value
    model.encode.return_value.tolist.return_value = [0.1, 0.2, 0.3]

    vector = query._embed_text("おはよう", "intfloat/multilingual-e5-base")

    assert vector == [0.1, 0.2, 0.3]
    model.encode.assert_called_once_with("query: おはよう")


@patch("sentence_transformers.SentenceTransformer", side_effect=OSError("network down"))
def test_embed_text_propagates_oserror(_: Mock) -> None:
    """モデルロード失敗は呼び出し元に伝播する。"""
    with pytest.raises(OSError):
        query._embed_text("おはよう", "intfloat/multilingual-e5-base")


@patch("sentence_transformers.SentenceTransformer")
def test_embed_text_propagates_runtime_error(mock_transformer: Mock) -> None:
    """encode 実行中の RuntimeError は伝播する。"""
    model = mock_transformer.return_value
    model.encode.side_effect = RuntimeError("encode failed")

    with pytest.raises(RuntimeError):
        query._embed_text("おはよう", "intfloat/multilingual-e5-base")


@patch("sentence_transformers.SentenceTransformer")
def test_embed_text_raises_value_error_on_empty_result(mock_transformer: Mock) -> None:
    """空の埋め込み結果は ValueError とする。"""
    model = mock_transformer.return_value
    model.encode.return_value.tolist.return_value = []

    with pytest.raises(ValueError):
        query._embed_text("おはよう", "intfloat/multilingual-e5-base")


@patch("nekochan_suggest.query._load_config")
@patch("nekochan_suggest.query._load_annotations")
@patch("nekochan_suggest.query._embed_text")
def test_suggest_returns_default_three_results(
    mock_embed_text: Mock,
    mock_load_annotations: Mock,
    mock_load_config: Mock,
) -> None:
    """count 省略時は 3 件返す。"""
    mock_load_config.return_value = {"embed_model": "intfloat/multilingual-e5-base"}
    mock_embed_text.return_value = [1.0, 0.0, 0.0]
    mock_load_annotations.return_value = _sample_annotations()

    results = query.suggest("うれしい")

    assert len(results) == 3
    assert all(isinstance(result, SuggestionResult) for result in results)


@patch("nekochan_suggest.query._load_config")
@patch("nekochan_suggest.query._load_annotations")
@patch("nekochan_suggest.query._embed_text")
def test_suggest_respects_explicit_count(
    mock_embed_text: Mock,
    mock_load_annotations: Mock,
    mock_load_config: Mock,
) -> None:
    """count 指定時はその件数だけ返す。"""
    mock_load_config.return_value = {"embed_model": "intfloat/multilingual-e5-base"}
    mock_embed_text.return_value = [1.0, 0.0, 0.0]
    mock_load_annotations.return_value = _sample_annotations()

    results = query.suggest("うれしい", count=2)

    assert len(results) == 2


@patch("nekochan_suggest.query._load_config")
@patch("nekochan_suggest.query._load_annotations")
@patch("nekochan_suggest.query._embed_text")
def test_suggest_returns_all_available_when_count_exceeds_records(
    mock_embed_text: Mock,
    mock_load_annotations: Mock,
    mock_load_config: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """利用可能件数を超える count は全件返す。"""
    mock_load_config.return_value = {"embed_model": "intfloat/multilingual-e5-base"}
    mock_embed_text.return_value = [1.0, 0.0, 0.0]
    mock_load_annotations.return_value = _sample_annotations()

    results = query.suggest("うれしい", count=10)
    captured = capsys.readouterr()

    assert len(results) == 6
    assert captured.err == ""


@patch("nekochan_suggest.query._load_config")
@patch("nekochan_suggest.query._load_annotations")
@patch("nekochan_suggest.query._embed_text")
def test_suggest_sorts_results_by_score_desc(
    mock_embed_text: Mock,
    mock_load_annotations: Mock,
    mock_load_config: Mock,
) -> None:
    """提案結果はスコア降順で並ぶ。"""
    mock_load_config.return_value = {"embed_model": "intfloat/multilingual-e5-base"}
    mock_embed_text.return_value = [1.0, 0.0, 0.0]
    mock_load_annotations.return_value = _sample_annotations()

    results = query.suggest("うれしい", count=3)

    assert [result.score for result in results] == sorted(
        [result.score for result in results],
        reverse=True,
    )


@pytest.mark.parametrize(
    ("text", "count"),
    [
        ("", 3),
        ("   ", 3),
        ("a" * 1001, 3),
        ("ok", 0),
        ("ok", 11),
    ],
)
def test_suggest_validation_raises_value_error(text: str, count: int) -> None:
    """不正な入力は ValueError を送出する。"""
    with pytest.raises(ValueError):
        query.suggest(text, count=count)


@patch("nekochan_suggest.query._load_config")
@patch("nekochan_suggest.query._load_annotations")
@patch("nekochan_suggest.query._embed_text")
def test_suggest_validation_accepts_boundary_counts(
    mock_embed_text: Mock,
    mock_load_annotations: Mock,
    mock_load_config: Mock,
) -> None:
    """境界値 1 と 10 は許可する。"""
    mock_load_config.return_value = {"embed_model": "intfloat/multilingual-e5-base"}
    mock_embed_text.return_value = [1.0, 0.0, 0.0]
    mock_load_annotations.return_value = _sample_annotations()

    one_result = query.suggest("ok", count=1)
    ten_results = query.suggest("ok", count=10)

    assert len(one_result) == 1
    assert len(ten_results) == 6


def _sample_annotations() -> list[dict[str, object]]:
    """suggest() テスト用の簡易アノテーション一覧を返す。"""
    return [
        {"name": "yatta-nya", "annotation": "joy", "embedding": [1.0, 0.0, 0.0]},
        {"name": "niko-nya", "annotation": "smile", "embedding": [0.9, 0.1, 0.0]},
        {"name": "hare-nya", "annotation": "sunny", "embedding": [0.8, 0.2, 0.0]},
        {"name": "nemui-nya", "annotation": "sleepy", "embedding": [0.2, 0.8, 0.0]},
        {"name": "kyukei-nya", "annotation": "rest", "embedding": [0.1, 0.9, 0.0]},
        {"name": "okoru-nya", "annotation": "angry", "embedding": [0.0, 0.0, 1.0]},
    ]


# ---------------------------------------------------------------------------
# _load_config() の gif_max_frames テスト — T010
# ---------------------------------------------------------------------------


class TestLoadConfigGifMaxFrames:
    """_load_config() の gif_max_frames キーに関するテスト。"""

    def test_default_gif_max_frames_is_four(self) -> None:
        """環境変数未設定のとき gif_max_frames は '4' を返す。"""
        import os
        from unittest.mock import patch

        from nekochan_suggest.query import _load_config

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NEKOCHAN_GIF_MAX_FRAMES", None)
            config = _load_config()

        assert config["gif_max_frames"] == "4"

    def test_env_var_overrides_gif_max_frames(self) -> None:
        """NEKOCHAN_GIF_MAX_FRAMES=2 のとき gif_max_frames は '2' を返す。"""
        import os
        from unittest.mock import patch

        from nekochan_suggest.query import _load_config

        with patch.dict(os.environ, {"NEKOCHAN_GIF_MAX_FRAMES": "2"}):
            config = _load_config()

        assert config["gif_max_frames"] == "2"
