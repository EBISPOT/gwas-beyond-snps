from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button


class NavButtons(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button("Previous", id="back")
        # next buttons always started disabled until valid user input
        yield Button("Next", id="next", disabled=True)

    def on_button_pressed(self, event):
        if event.button.id == "next":
            self.app.next_screen()
        elif event.button.id == "back":
            self.app.previous_screen()
