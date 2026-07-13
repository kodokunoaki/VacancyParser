import tkinter as tk
from collections.abc import Sequence

import customtkinter as ctk

from app.ui.theme import COLORS, CONTROL_RADIUS, FONT_FAMILY


class LabeledEntry(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    def __init__(
        self,
        master: ctk.CTkFrame,
        label: str,
        variable: tk.StringVar,
        *,
        placeholder: str = "",
        suffix: str | None = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=label,
            anchor="w",
            text_color=COLORS.text_muted,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", pady=(0, 7))

        self.input_shell = ctk.CTkFrame(
            self,
            height=44,
            fg_color=COLORS.field,
            border_color=COLORS.border,
            border_width=1,
            corner_radius=CONTROL_RADIUS,
        )
        self.input_shell.grid(row=1, column=0, sticky="ew")
        self.input_shell.grid_propagate(False)
        self.input_shell.columnconfigure(0, weight=1)
        self.input_shell.rowconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self.input_shell,
            textvariable=variable,
            placeholder_text=placeholder,
            height=40,
            border_width=0,
            fg_color=COLORS.field,
            text_color=COLORS.text,
            placeholder_text_color=COLORS.text_faint,
            corner_radius=CONTROL_RADIUS - 2,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
        )
        entry_padx = (1, 0) if suffix is not None else 1
        self.entry.grid(row=0, column=0, sticky="nsew", padx=entry_padx, pady=1)
        self.entry.bind("<FocusIn>", self._show_focus, add="+")
        self.entry.bind("<FocusOut>", self._hide_focus, add="+")

        if suffix is not None:
            ctk.CTkFrame(
                self.input_shell,
                width=1,
                fg_color=COLORS.border,
                corner_radius=0,
            ).grid(row=0, column=1, sticky="ns", pady=1)
            ctk.CTkLabel(
                self.input_shell,
                text=suffix,
                width=54,
                text_color=COLORS.text_muted,
                fg_color=COLORS.surface_hover,
                corner_radius=CONTROL_RADIUS - 2,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            ).grid(row=0, column=2, sticky="nsew", padx=(0, 1), pady=1)

    def set_enabled(self, enabled: bool) -> None:
        self.entry.configure(state="normal" if enabled else "disabled")

    def _show_focus(self, _event: tk.Event) -> None:
        self.input_shell.configure(border_color=COLORS.border_focus)

    def _hide_focus(self, _event: tk.Event) -> None:
        self.input_shell.configure(border_color=COLORS.border)


class LabeledComboBox(ctk.CTkFrame):  # pylint: disable=too-many-ancestors
    def __init__(
        self,
        master: ctk.CTkFrame,
        label: str,
        variable: tk.StringVar,
        values: Sequence[str],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=label,
            anchor="w",
            text_color=COLORS.text_muted,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", pady=(0, 7))

        self.input_shell = ctk.CTkFrame(
            self,
            height=44,
            fg_color=COLORS.field,
            border_color=COLORS.border,
            border_width=1,
            corner_radius=CONTROL_RADIUS,
        )
        self.input_shell.grid(row=1, column=0, sticky="ew")
        self.input_shell.grid_propagate(False)
        self.input_shell.columnconfigure(0, weight=1)
        self.input_shell.rowconfigure(0, weight=1)

        self.combo = ctk.CTkComboBox(
            self.input_shell,
            values=list(values),
            variable=variable,
            state="readonly",
            height=40,
            fg_color=COLORS.field,
            border_width=0,
            button_color=COLORS.surface_hover,
            button_hover_color=COLORS.surface_hover,
            dropdown_fg_color=COLORS.surface,
            dropdown_hover_color=COLORS.surface_hover,
            dropdown_text_color=COLORS.text,
            text_color=COLORS.text,
            corner_radius=CONTROL_RADIUS - 2,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=14),
        )
        self.combo.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

    def set_enabled(self, enabled: bool) -> None:
        self.combo.configure(state="readonly" if enabled else "disabled")
