from __future__ import annotations

import logging

from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button

logger = logging.getLogger(__name__)


class WizardScreen(Screen):
    can_proceed: bool = reactive(False)

    def watch_can_proceed(self, value: bool) -> None:
        # find the next navbar button inside this screen
        try:
            next_btn = self.query_one("#next", Button)
        except NoMatches:
            logger.info("No next button")
        else:
            next_btn.disabled = not value
