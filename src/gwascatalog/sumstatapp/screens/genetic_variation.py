from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, RadioButton, RadioSet, Rule

from gwascatalog.sumstatapp.navbuttons import NavButtons


class GeneticVariationScreen(Screen):
    name = "genetic_variation"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("What kind of genetic variation have you studied?")
            yield Rule()
            with RadioSet():
                yield RadioButton(
                    "Single-nucleotide polymorphism (SNP)", id="snp-variants"
                )
                yield RadioButton("Copy number variant (CNV)")
                yield RadioButton("Genes")
                yield RadioButton("I'm not sure")
            yield NavButtons()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed and event.pressed.id == "snp-variants":
            self.app.push_screen(BadVariationWarning())


class BadVariationWarning(Screen):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(
                "Currently only CNV and Gene-based GWAS can be submitted using this tool. \n\n"
                "Please see gwas-sumstats-tools for SNP submissions: "
                "[link='https://github.com/ebispot/gwas-sumstats-tools']https://github.com/ebispot/gwas-sumstats-tools[/link]",
                variant="warning",
            )
            yield Rule()
            with Horizontal():
                yield Button("Back", id="back")
                yield Button("Quit", id="quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "back":
            self.app.pop_screen()  # go back to the previous screen
        elif button_id == "quit":
            self.app.exit()
