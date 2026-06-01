from aiogram.types import InlineKeyboardMarkup

from moex_analyst.presentation.bot.callbacks import (
    AnalyzeCallback,
    MenuAction,
    MenuCallback,
)
from moex_analyst.presentation.bot.keyboards import main_menu_keyboard, watchlist_keyboard


class TestMainMenuKeyboard:
    def test_returns_inline_keyboard_markup(self) -> None:
        kb = main_menu_keyboard()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_five_buttons(self) -> None:
        kb = main_menu_keyboard()
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 5

    def test_all_actions_represented(self) -> None:
        kb = main_menu_keyboard()
        actions: set[str] = set()
        for row in kb.inline_keyboard:
            for btn in row:
                actions.add(btn.callback_data)
        expected = {MenuCallback(action=a).pack() for a in MenuAction}
        assert actions == expected

    def test_buttons_have_text(self) -> None:
        kb = main_menu_keyboard()
        for row in kb.inline_keyboard:
            for btn in row:
                assert btn.text


class TestWatchlistKeyboard:
    def test_one_button_per_ticker(self) -> None:
        kb = watchlist_keyboard(["SNGS", "VTBR", "SGZH"])
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 3

    def test_empty_tickers(self) -> None:
        kb = watchlist_keyboard([])
        total = sum(len(row) for row in kb.inline_keyboard)
        assert total == 0

    def test_buttons_carry_correct_callback(self) -> None:
        tickers = ["SNGS", "VTBR"]
        kb = watchlist_keyboard(tickers)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert texts == tickers

    def test_callback_data_matches_ticker(self) -> None:
        kb = watchlist_keyboard(["SNGS"])
        btn = kb.inline_keyboard[0][0]
        data = btn.callback_data
        unpacked = AnalyzeCallback.unpack(data)
        assert unpacked.ticker == "SNGS"
