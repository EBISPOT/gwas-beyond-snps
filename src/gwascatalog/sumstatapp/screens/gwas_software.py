from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Label, RadioButton, RadioSet, Rule

from gwascatalog.sumstatapp.navbuttons import NavButtons


class GWASSoftwareScreen(Screen):
    """
    Screen for selecting the software used for GWAS analysis.

    This screen allows the user to indicate which GWAS software they used.

    We ask this because some software outputs zero p-values, but generally speaking
    p-values never be zero in statistical frameworks (like Cromwell's rule, "... think
    it possible that you may be mistaken").

    As a compromise the GWAS Catalog grudgingly accepts zero p-values but the offending
    software must be specified.
    """

    name = "software"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("What software did you use to do your GWAS analysis?")
            yield Label("p-values must never be zero", variant="warning")
            yield Rule()
            with RadioSet():
                yield RadioButton("BOLT-LMM")
                yield RadioButton("REGENIE")
                yield RadioButton("SNP-test")
                yield RadioButton("SAIGE")
                yield RadioButton("Other software")

            yield NavButtons()
