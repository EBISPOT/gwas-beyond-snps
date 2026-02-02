from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, RadioButton, RadioSet, Rule

from gwascatalog.sumstatapp.navbuttons import NavButtons


class EffectSizeScreen(Screen):
    name = "effect_size"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("How have you measured the effect size of your variants?")
            yield Rule()
            with RadioSet():
                yield RadioButton("Beta")
                yield RadioButton("Odds ratio")
                yield RadioButton("Z-score")
                yield RadioButton(
                    "My statistical model can't measure effect size",
                    id="no-effect-size",
                )

            yield NavButtons()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed and event.pressed.id == "no-effect-size":
            self.app.push_screen(NoEffectSizeWarning())


class NoEffectSizeWarning(Screen):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(
                "All CNV and SNP submissions to the GWAS Catalog must "
                "include an effect size estimate.",
                variant="warning",
            )
            yield Rule()
            yield Label(
                "However, effect sizes are optional (but encouraged) for gene-based GWAS.",
                variant="primary",
            )
            yield Rule()
            yield Button("OK", id="ok")

    def on_button_pressed(self) -> None:
        self.app.pop_screen()
