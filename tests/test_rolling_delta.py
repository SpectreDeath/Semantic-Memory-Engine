from src.scribe.rolling_delta import RollingDelta


class FakePyStyl:
    def compare_texts(self, window_text, ref_text, top_n=100):
        return len(window_text.split()) + len(ref_text.split())


def test_generate_windows_yields_token_windows():
    text = "one two three four five six seven eight nine ten eleven twelve"
    windows = list(RollingDelta().generate_windows(text, window_size=5, step=2))

    assert len(windows) == 4
    assert windows[0][0] == 0
    assert windows[-1][0] == 6
    assert windows[0][1] == "one two three four five"


def test_analyze_rolling_delta_uses_injected_pystyl():
    analyzer = RollingDelta.__new__(RollingDelta)
    analyzer.pystyl = FakePyStyl()

    result = analyzer.analyze_rolling_delta(
        "one two three four five six seven",
        {"alpha": "alpha beta", "bravo": "bravo"},
        window_size=3,
        step=1,
    )

    assert result["windows"] == [0, 1, 2, 3, 4]
    assert result["series"]["alpha"] == [5, 5, 5, 5, 5]
    assert result["series"]["bravo"] == [4, 4, 4, 4, 4]
    assert result["volatility"]["alpha"] == 0.0


def test_analyze_rolling_delta_returns_errors_for_missing_inputs():
    analyzer = RollingDelta.__new__(RollingDelta)
    analyzer.pystyl = FakePyStyl()

    assert analyzer.analyze_rolling_delta("text", {}, window_size=2) == {
        "error": "No candidates provided"
    }

    analyzer.pystyl = None
    assert analyzer.analyze_rolling_delta("text", {"alpha": "alpha"}) == {
        "error": "PyStylWrapper not initialized"
    }
