from moex_analyst.presentation.bot.callbacks import (
    AnalyzeCallback,
    AnalyzeTypeCallback,
    MenuAction,
    MenuCallback,
    TickerCallback,
    TimeframeCallback,
)


class TestMenuAction:
    def test_enum_values(self) -> None:
        assert MenuAction.MAIN_MENU == "main_menu"
        assert MenuAction.BACK == "back"
        assert MenuAction.MARKET == "market"
        assert MenuAction.BEST == "best"
        assert MenuAction.WORST == "worst"
        assert MenuAction.WATCHLIST == "watchlist"
        assert MenuAction.HELP == "help"
        assert MenuAction.SIGNALS == "signals"
        assert MenuAction.STATISTICS == "statistics"
        assert MenuAction.SETTINGS == "settings"
        assert MenuAction.ANALYZE == "analyze"
        assert MenuAction.CUSTOM_TICKER == "custom_ticker"

    def test_all_actions_covered(self) -> None:
        expected = {
            "main_menu",
            "back",
            "market",
            "best",
            "worst",
            "watchlist",
            "help",
            "signals",
            "statistics",
            "settings",
            "analyze",
            "custom_ticker",
        }
        assert {a.value for a in MenuAction} == expected


class TestMenuCallback:
    def test_prefix(self) -> None:
        assert MenuCallback.__prefix__ == "menu"

    def test_pack_and_unpack(self) -> None:
        original = MenuCallback(action=MenuAction.MARKET)
        packed = original.pack()
        unpacked = MenuCallback.unpack(packed)
        assert unpacked.action == MenuAction.MARKET

    def test_all_actions_roundtrip(self) -> None:
        for action in MenuAction:
            original = MenuCallback(action=action)
            packed = original.pack()
            unpacked = MenuCallback.unpack(packed)
            assert unpacked.action == action


class TestTickerCallback:
    def test_prefix(self) -> None:
        assert TickerCallback.__prefix__ == "ticker"

    def test_pack_and_unpack(self) -> None:
        original = TickerCallback(ticker="SNGS")
        packed = original.pack()
        unpacked = TickerCallback.unpack(packed)
        assert unpacked.ticker == "SNGS"


class TestTimeframeCallback:
    def test_prefix(self) -> None:
        assert TimeframeCallback.__prefix__ == "tf"

    def test_pack_and_unpack(self) -> None:
        original = TimeframeCallback(value="1H")
        packed = original.pack()
        unpacked = TimeframeCallback.unpack(packed)
        assert unpacked.value == "1H"


class TestAnalyzeTypeCallback:
    def test_prefix(self) -> None:
        assert AnalyzeTypeCallback.__prefix__ == "atype"

    def test_pack_and_unpack(self) -> None:
        original = AnalyzeTypeCallback(type_="full")
        packed = original.pack()
        unpacked = AnalyzeTypeCallback.unpack(packed)
        assert unpacked.type_ == "full"


class TestAnalyzeCallback:
    def test_prefix(self) -> None:
        assert AnalyzeCallback.__prefix__ == "analyze"

    def test_pack_and_unpack(self) -> None:
        original = AnalyzeCallback(ticker="SNGS")
        packed = original.pack()
        unpacked = AnalyzeCallback.unpack(packed)
        assert unpacked.ticker == "SNGS"

    def test_empty_ticker(self) -> None:
        original = AnalyzeCallback(ticker="")
        packed = original.pack()
        unpacked = AnalyzeCallback.unpack(packed)
        assert unpacked.ticker == ""

    def test_serialized_data_is_not_empty(self) -> None:
        cb = AnalyzeCallback(ticker="SNGS")
        packed = cb.pack()
        assert "SNGS" in packed
        assert "analyze" in packed
