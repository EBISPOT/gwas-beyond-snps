from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import DirectoryTree, Label, Rule

from gwascatalog.sumstatapp.constants import VALID_SUMSTAT_SUFFIXES
from gwascatalog.sumstatapp.navbuttons import NavButtons

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class FilePickerScreen(Screen):
    name = "file_picker"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Select the file containing your summary statistics")
            yield Rule()
            yield FilteredDirectoryTree(".")
            yield NavButtons()


class FilteredDirectoryTree(DirectoryTree):
    show_only_valid_files: reactive[bool] = reactive(True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        for path in paths:
            if (
                path.is_dir()
                and not path.name.startswith(".")
                and not path.name.startswith("__")
            ):
                yield path
            if path.is_file() and not path.name.startswith("."):
                if (
                    self.show_only_valid_files
                    and "".join(path.suffixes) in VALID_SUMSTAT_SUFFIXES
                    or not self.show_only_valid_files
                ):
                    yield path
