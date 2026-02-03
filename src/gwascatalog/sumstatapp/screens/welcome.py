from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Rule, Static

from gwascatalog.sumstatapp.navbuttons import NavButtons
from gwascatalog.sumstatapp.screens.base_wizard_screen import WizardScreen

WELCOME_TITLE = "Welcome to the [link='https://ebi.ac.uk/gwas']GWAS Catalog[/link] summary statistics tool 🧬🧪 "
WELCOME_MSG = (
    "This tool will check your summary statistics files are valid and automatically create new files ready for submission.\n\n"
    "If you need help press ? or email [link='mailto:gwas-subs@ebi.ac.uk']gwas-subs@ebi.ac.uk[/link]\n\n"
    "Thank you for submitting your data to the GWAS Catalog ❤️\n\n"
)


class WelcomeScreen(WizardScreen):
    name = "welcome"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(WELCOME_TITLE, id="title")
            yield Rule()
            yield Static(WELCOME_MSG)
            yield NavButtons()

    def on_mount(self):
        # no previous button on the welcome screen
        prev_button = self.query_one("#back", Button)
        prev_button.remove()

    def on_screen_resume(self):
        # send a message that we're ready to proceed
        # (no user input needed)
        self.can_proceed = True
