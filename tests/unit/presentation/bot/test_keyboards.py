from aiogram.types import InlineKeyboardMarkup

from moex_analyst.infrastructure.moex.config import INSTRUMENT_REGISTRY
from moex_analyst.presentation.bot.callbacks import (
    AnalyzeCallback,
    AnalyzeTypeCallback,
    MenuAction,
    MenuCallback,
    TickerCallback,
    TimeframeCallback,
)
from moex_analyst.presentation.bot.formatters.text import fmt_instrument_menu, fmt_instrument_name
from moex_analyst.presentation.bot.keyboards import (
    analysis_type_keyboard,
    back_home_keyboard,
    main_menu_keyboard,
    result_keyboard,
    ticker_selection_keyboard,
    timeframe_keyboard,
    watchlist_keyboard,
)


class TestMainMenuKeyboard:
    def test_returns_inline_keyboard_markup(self) -> None:
        kb = main_menu_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_seven_buttons(self) -> None:
        kb = main_menu_keyboard()
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 7

    def test_all_menu_actions_represented(self) -> None:
        kb = main_menu_keyboard()
        actions: set[str] = set()
        for row in kb.inline_keyboard:
            for btn in row:
                actions.add(btn.callback_data)
        menu_actions = {
            MenuAction.ANALYZE,
            MenuAction.MARKET,
            MenuAction.WATCHLIST,
            MenuAction.SIGNALS,
            MenuAction.STATISTICS,
            MenuAction.SETTINGS,
            MenuAction.HELP,
        }
        expected = {MenuCallback(action=a).pack() for a in menu_actions}
        assert actions == expected

    def test_buttons_have_text(self) -> None:
        kb = main_menu_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert btn.text


class TestBackHomeKeyboard:
    def test_returns_inline_keyboard_markup(self) -> None:
        kb = back_home_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_two_buttons(self) -> None:
        kb = back_home_keyboard()
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 2

    def test_buttons_have_back_and_home_text(self) -> None:
        kb = back_home_keyboard()
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert any("Назад" in t for t in texts)
        assert any("Главное меню" in t for t in texts)

    def test_all_buttons_go_to_main_menu(self) -> None:
        kb = back_home_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                unpacked = MenuCallback.unpack(btn.callback_data)
                assert unpacked.action == MenuAction.MAIN_MENU


class TestTickerSelectionKeyboard:
    def test_returns_inline_keyboard_markup(self) -> None:
        kb = ticker_selection_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_ticker_buttons_and_nav(self) -> None:
        kb = ticker_selection_keyboard()
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert fmt_instrument_menu("SNGS") in texts
        assert fmt_instrument_menu("IMOEX") in texts
        assert "🔍 Ввести свой тикер" in texts
        assert "Назад" in " ".join(texts)
        assert "Главное меню" in " ".join(texts)

    def test_ticker_buttons_carry_ticker_callback(self) -> None:
        kb = ticker_selection_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                try:
                    unpacked = TickerCallback.unpack(btn.callback_data)
                except Exception:
                    continue
                assert unpacked.ticker in INSTRUMENT_REGISTRY
                expected = fmt_instrument_menu(unpacked.ticker)
                assert btn.text == expected


class TestTimeframeKeyboard:
    def test_returns_inline_keyboard_markup(self) -> None:
        kb = timeframe_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_timeframe_buttons_and_nav(self) -> None:
        kb = timeframe_keyboard()
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        for tf in ("15M", "1H", "4H", "1D", "1W"):
            assert tf in texts
        assert "Назад" in " ".join(texts)
        assert "Главное меню" in " ".join(texts)

    def test_timeframe_buttons_carry_timeframe_callback(self) -> None:
        kb = timeframe_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                if btn.text in ("15M", "1H", "4H", "1D", "1W"):
                    data = btn.callback_data
                    unpacked = TimeframeCallback.unpack(data)
                    assert unpacked.value == btn.text


class TestAnalysisTypeKeyboard:
    def test_returns_inline_keyboard_markup(self) -> None:
        kb = analysis_type_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_analysis_type_and_nav(self) -> None:
        kb = analysis_type_keyboard()
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert "Полный анализ" in " ".join(texts)
        assert "Назад" in " ".join(texts)
        assert "Главное меню" in " ".join(texts)

    def test_full_analysis_button_carry_type_callback(self) -> None:
        kb = analysis_type_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                if "Полный анализ" in btn.text:
                    data = btn.callback_data
                    unpacked = AnalyzeTypeCallback.unpack(data)
                    assert unpacked.type_ == "full"


class TestResultKeyboard:
    def test_returns_inline_keyboard_markup(self) -> None:
        kb = result_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_nav_buttons(self) -> None:
        kb = result_keyboard()
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert "Назад" in " ".join(texts)
        assert "Главное меню" in " ".join(texts)

    def test_has_two_buttons(self) -> None:
        kb = result_keyboard()
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 2


class TestWatchlistKeyboard:
    def test_one_button_per_ticker(self) -> None:
        kb = watchlist_keyboard(["SNGS", "VTBR", "SGZH"])
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total >= 3

    def test_empty_tickers(self) -> None:
        kb = watchlist_keyboard([])
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total >= 2  # back + home

    def test_buttons_carry_correct_text(self) -> None:
        kb = watchlist_keyboard(["SNGS", "VTBR"])
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert fmt_instrument_name("SNGS") in texts
        assert fmt_instrument_name("VTBR") in texts

    def test_ticker_buttons_carry_analyze_callback(self) -> None:
        kb = watchlist_keyboard(["SNGS"])
        for row in kb.inline_keyboard:
            for btn in row:
                try:
                    unpacked = AnalyzeCallback.unpack(btn.callback_data)
                except Exception:
                    continue
                assert unpacked.ticker == "SNGS"
                assert btn.text == fmt_instrument_name("SNGS")
