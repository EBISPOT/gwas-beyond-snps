from __future__ import annotations

from textual.app import App

from gwascatalog.sumstatapp.screens import (
    EffectSizeScreen,
    FilePickerScreen,
    GeneticVariationScreen,
    GWASSoftwareScreen,
    WelcomeScreen,
)


class SumstatWizardApp(App):
    CSS_PATH = "wizard.tcss"
    SCREENS = {
        "welcome": WelcomeScreen,
        "effect_size": EffectSizeScreen,
        "genetic_variation": GeneticVariationScreen,
        "software": GWASSoftwareScreen,
        "file_picker": FilePickerScreen,
    }

    SCREEN_ORDER = [
        "welcome",
        "genetic_variation",
        "effect_size",
        "software",
        "file_picker",
    ]

    def on_mount(self) -> None:
        """Start the application on the welcome screen"""
        self.push_screen(WelcomeScreen(name="welcome"))

    @property
    def current_index(self) -> int:
        return self.SCREEN_ORDER.index(self.screen.name)

    def next_screen(self) -> None:
        idx = self.current_index
        if idx + 1 < len(self.SCREEN_ORDER):
            next_name = self.SCREEN_ORDER[idx + 1]
            self.push_screen(next_name)

    def previous_screen(self) -> None:
        idx = self.current_index
        if idx > 0:
            prev_name = self.SCREEN_ORDER[idx - 1]
            self.push_screen(prev_name)


if __name__ == "__main__":
    app = SumstatWizardApp()
    app.run()
