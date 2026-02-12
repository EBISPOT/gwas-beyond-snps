from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Collapsible,
    Label,
    RadioButton,
    RadioSet,
    Rule,
    Static,
)

from gwascatalog.sumstatapp.navbuttons import NavButtons
from gwascatalog.sumstatapp.screens.base_wizard_screen import WizardScreen


class EffectSizeScreen(WizardScreen):
    name = "effect_size"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("How have you measured the effect size of your variants?")
            with Collapsible(title="Why do we ask this?"):
                yield Label(
                    "Effect size and uncertainty measurements are mandatory for most GWAS submissions.\n"
                    "This is because we like to be difficult and make your day worse."
                )

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
            self.can_proceed = False
        else:
            self.can_proceed = True


class NoEffectSizeWarning(Screen):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                "All CNV and SNP submissions to the GWAS Catalog must "
                "include an effect size estimate. Please contact [link='mailto:gwas-subs@ebi.ac.uk']gwas-subs@ebi.ac.uk[/link] if you have any questions or need help.",
            )
            yield Rule()
            yield Static(
                "However, effect sizes are optional (but encouraged) for gene-based GWAS.",
            )
            yield Rule()
            yield Button("OK", id="ok")

    def on_button_pressed(self) -> None:
        self.app.pop_screen()
