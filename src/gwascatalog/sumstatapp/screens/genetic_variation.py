from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
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


class GeneticVariationScreen(WizardScreen):
    name = "genetic_variation"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("What kind of genetic variation have you studied?")
            with Collapsible(title="Why do we ask this?"):
                yield Label(
                    "Different types of genetic variants have different data requirements.\n"
                    "For example, structural variants like CNVs require start and end positions (a range), while SNPs only require a single position."
                )

            yield Rule()
            with RadioSet():
                yield RadioButton(
                    "Single-nucleotide polymorphism (SNP)", id="snp-variants"
                )
                yield RadioButton("Copy number variant (CNV)")
                yield RadioButton("Genes")
                yield RadioButton("Something else", id="something-else")
            yield NavButtons()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed and event.pressed.id == "snp-variants":
            self.app.push_screen(BadVariationWarning())
            self.can_proceed = False
        elif event.pressed and event.pressed.id == "something-else":
            self.app.push_screen(SomethingElseScreen())
            self.can_proceed = False
        else:
            self.can_proceed = True


class BadVariationWarning(Screen):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Rule()
            yield Static(
                "Currently only CNV and Gene-based GWAS can be submitted using this tool."
            )
            yield Rule()
            yield Static(
                "Please see gwas-sumstats-tools for SNP submissions: "
                "[link='https://github.com/ebispot/gwas-sumstats-tools']https://github.com/ebispot/gwas-sumstats-tools[/link]",
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


class SomethingElseScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Rule()
            yield Static(
                "Only SNP based, CNV-based and gene-based genome-wide studies "
                "are currently validated by the GWAS catalog."
            )
            yield Rule()
            yield Static(
                "To enquire about submitting a non-standard data "
                "type, please contact [link='mailto:gwas-subs@ebi.ac.uk']gwas-subs@ebi.ac.uk[/link].",
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
