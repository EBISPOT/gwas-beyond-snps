from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Collapsible, RadioButton, RadioSet, Rule, Static

from gwascatalog.sumstatapp.navbuttons import NavButtons
from gwascatalog.sumstatapp.screens.base_wizard_screen import WizardScreen


class PValueTypeScreen(WizardScreen):
    name = "p_value"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                "How are [i]p[/i] values represented in your data?", markup=True
            )
            with Collapsible(title="Why do we ask this?"):
                yield Static(
                    "The GWAS Catalog accepts standard [i]p[/i] values or negative log10 [i]p[/i] values (not both)",
                    markup=True,
                )

            yield Rule()
            with RadioSet():
                yield RadioButton("[i]p[/i]")
                yield RadioButton("negative log10 [i]p[/i]")

            yield NavButtons()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed:
            self.can_proceed = True
