from moex_analyst.presentation.bot.callbacks import AnalyzeCallback, MenuAction, MenuCallback


class TestMenuAction:
    def test_enum_values(self) -> None:
        assert MenuAction.MARKET == "market"
        assert MenuAction.BEST == "best"
        assert MenuAction.WORST == "worst"
        assert MenuAction.WATCHLIST == "watchlist"
        assert MenuAction.HELP == "help"

    def test_all_actions_covered(self) -> None:
        expected = {"market", "best", "worst", "watchlist", "help"}
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
