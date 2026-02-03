from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Collapsible,
    RadioButton,
    RadioSet,
    Rule,
    Static,
)

from gwascatalog.sumstatapp.navbuttons import NavButtons
from gwascatalog.sumstatapp.screens.base_wizard_screen import WizardScreen


class HighlySignificantScreen(WizardScreen):
    name = "highly_significant"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                "Are highly significant [i]p[/i] values thresholded or rounded to zero?",
                markup=True,
            )
            with Collapsible(title="Why do we ask this?"):
                yield Static(
                    "Thresholding or rounding [i]p[/i] values limits the downstream usability of the data."
                )
                yield Static(
                    "If your data includes [i]p[/i] values thresholded or rounded to zero please provide negative log10 [i]p[/i] values instead.",
                    markup=True,
                )

            yield Rule()
            with RadioSet():
                yield RadioButton("No")
                yield RadioButton("Yes", id="thresholded-p-values")

            yield NavButtons()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed and event.pressed.id == "thresholded-p-values":
            self.app.push_screen(ThresholdedPValueWarning())
            self.can_proceed = True
        else:
            self.can_proceed = True


class ThresholdedPValueWarning(Screen):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Rule()
            yield Static(
                "If your data includes [i]p[/i] values thresholded or rounded to zero please provide negative log10 [i]p[/i] values instead.",
                markup=True,
            )
            yield Rule()
            yield Static(
                "If this isn't possible, you will be asked to include more details "
                "about the GWAS software that you used in the study metadata. ",
                markup=True,
            )
            yield Rule()
            with Collapsible(title="Why do we ask this?"):
                yield Static(
                    "We ask this because it's important for users of the data to "
                    "understand the precision of the software that was used to "
                    "calculate the [i]p[/i] values.",
                    markup=True,
                )
            yield Rule()
            with Horizontal():
                yield Button("Back", id="back")
                yield Button("Quit", id="quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "back":
            self.app.pop_screen()
        elif button_id == "quit":
            self.app.exit()
