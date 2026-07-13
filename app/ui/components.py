import tkinter as tk
from collections.abc import Sequence

import customtkinter as ctk

from app.ui.theme import COLORS, CONTROL_RADIUS, FONT_FAMILY


class LabeledEntry(ctk.CTkFrame):
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

        self.entry = ctk.CTkEntry(
            self.input_shell,
            textvariable=variable,
            placeholder_text=placeholder,
            height=42,
            border_width=0,
            fg_color="transparent",
            text_color=COLORS.text,
            placeholder_text_color=COLORS.text_faint,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
        )
        self.entry.grid(row=0, column=0, sticky="nsew", padx=(4, 0))
        self.entry.bind("<FocusIn>", self._show_focus, add="+")
        self.entry.bind("<FocusOut>", self._hide_focus, add="+")

        if suffix is not None:
            ctk.CTkLabel(
                self.input_shell,
                text=suffix,
                width=54,
                text_color=COLORS.text_muted,
                fg_color=COLORS.surface_hover,
                corner_radius=CONTROL_RADIUS,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            ).grid(row=0, column=1, sticky="ns", padx=1, pady=1)

    def set_enabled(self, enabled: bool) -> None:
        self.entry.configure(state="normal" if enabled else "disabled")

    def _show_focus(self, _event: tk.Event) -> None:
        self.input_shell.configure(border_color=COLORS.border_focus)

    def _hide_focus(self, _event: tk.Event) -> None:
        self.input_shell.configure(border_color=COLORS.border)


class LabeledComboBox(ctk.CTkFrame):
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

        self.combo = ctk.CTkComboBox(
            self,
            values=list(values),
            variable=variable,
            state="readonly",
            height=44,
            fg_color=COLORS.field,
            border_color=COLORS.border,
            button_color=COLORS.field,
            button_hover_color=COLORS.surface_hover,
            dropdown_fg_color=COLORS.surface,
            dropdown_hover_color=COLORS.surface_hover,
            dropdown_text_color=COLORS.text,
            text_color=COLORS.text,
            corner_radius=CONTROL_RADIUS,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=14),
        )
        self.combo.grid(row=1, column=0, sticky="ew")

    def set_enabled(self, enabled: bool) -> None:
        self.combo.configure(state="readonly" if enabled else "disabled")
