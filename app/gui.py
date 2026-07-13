import queue
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox

import customtkinter as ctk

from app.core.config import settings
from app.gui_config import (
    ITEMS_ON_PAGE_OPTIONS,
    build_gui_config,
    output_name_without_csv,
)
from app.gui_controller import ParserController
from app.schemas import ParserEvent, ParserEventType
from app.ui.components import LabeledComboBox, LabeledEntry
from app.ui.theme import (
    COLORS,
    CONTROL_RADIUS,
    FONT_FAMILY,
    MONOSPACE_FONT_FAMILY,
    PANEL_RADIUS,
    SIDEBAR_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_SIZE,
)


@dataclass(frozen=True)
class GuiVariables:
    search_query: tk.StringVar
    salary: tk.StringVar
    max_pages: tk.StringVar
    output_file: tk.StringVar
    items_on_page: tk.StringVar
    status: tk.StringVar
    empty_title: tk.StringVar
    empty_description: tk.StringVar


@dataclass(frozen=True)
class FormWidgets:
    query: LabeledEntry
    salary: LabeledEntry
    pages: LabeledEntry
    items: LabeledComboBox
    output: LabeledEntry
    start_button: ctk.CTkButton

    @property
    def fields(self) -> tuple[LabeledEntry | LabeledComboBox, ...]:
        return self.query, self.salary, self.pages, self.items, self.output


@dataclass(frozen=True)
class ActivityWidgets:
    clear_button: ctk.CTkButton
    log: ctk.CTkTextbox
    empty_state: ctk.CTkFrame
    progress: ctk.CTkProgressBar


@dataclass(frozen=True)
class GuiWidgets:
    form: FormWidgets
    activity: ActivityWidgets
    status_dot: ctk.CTkLabel


class ParserApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.events: queue.Queue[ParserEvent] = queue.Queue()
        self.controller = ParserController(self.events)
        self._event_job: str | None = None
        self._has_log_content = False

        self.variables = GuiVariables(
            search_query=tk.StringVar(value=settings.search_query),
            salary=tk.StringVar(value=str(settings.salary)),
            max_pages=tk.StringVar(value=str(settings.max_pages)),
            output_file=tk.StringVar(
                value=output_name_without_csv(settings.output_file)
            ),
            items_on_page=tk.StringVar(value=str(settings.items_on_page)),
            status=tk.StringVar(value="Готово к запуску"),
            empty_title=tk.StringVar(value="Поиск ещё не запускался"),
            empty_description=tk.StringVar(
                value="Здесь появится прогресс и журнал операций"
            ),
        )

        self._configure_window()
        self.widgets = self._build_layout()
        self._set_running(False)
        self._event_job = self.root.after(100, self._process_events)

    def _configure_window(self) -> None:
        self.root.title("HH Parser")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.root.configure(fg_color=COLORS.window)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_layout(self) -> GuiWidgets:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_header()

        workspace = ctk.CTkFrame(self.root, fg_color="transparent")
        workspace.grid(row=1, column=0, sticky="nsew", padx=20, pady=(8, 16))
        workspace.columnconfigure(0, minsize=SIDEBAR_WIDTH)
        workspace.columnconfigure(1, weight=1)
        workspace.rowconfigure(0, weight=1)

        return GuiWidgets(
            form=self._build_settings_panel(workspace),
            activity=self._build_activity_panel(workspace),
            status_dot=self._build_status_bar(),
        )

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.root, fg_color="transparent", height=82)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        header.grid_propagate(False)
        header.columnconfigure(1, weight=1)

        mark = ctk.CTkFrame(
            header,
            width=54,
            height=54,
            fg_color="transparent",
            border_color=COLORS.accent,
            border_width=1,
            corner_radius=12,
        )
        mark.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 15), pady=6)
        mark.grid_propagate(False)
        ctk.CTkLabel(
            mark,
            text="HH",
            text_color=COLORS.accent,
            font=ctk.CTkFont(family=FONT_FAMILY, size=21, weight="bold"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            header,
            text="HH Parser",
            anchor="w",
            text_color=COLORS.text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
        ).grid(row=0, column=1, sticky="sw", pady=(7, 0))
        ctk.CTkLabel(
            header,
            text="Сбор вакансий hh.ru в CSV",
            anchor="w",
            text_color=COLORS.text_muted,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        ).grid(row=1, column=1, sticky="nw", pady=(1, 7))

    def _panel(self, master: ctk.CTkFrame) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            master,
            fg_color=COLORS.surface,
            border_color=COLORS.border,
            border_width=1,
            corner_radius=PANEL_RADIUS,
        )

    def _build_settings_panel(self, workspace: ctk.CTkFrame) -> FormWidgets:
        panel = self._panel(workspace)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(6, weight=1)

        ctk.CTkLabel(
            panel,
            text="Параметры поиска",
            anchor="w",
            text_color=COLORS.text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 16))

        query_field = LabeledEntry(
            panel,
            "Поисковый запрос",
            self.variables.search_query,
            placeholder="Например: Python-разработчик",
        )
        query_field.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 13))

        numeric_row = ctk.CTkFrame(panel, fg_color="transparent")
        numeric_row.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 13))
        numeric_row.columnconfigure((0, 1), weight=1)

        salary_field = LabeledEntry(
            numeric_row,
            "Зарплата от",
            self.variables.salary,
            placeholder="100000",
            suffix="₽",
        )
        salary_field.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        pages_field = LabeledEntry(
            numeric_row,
            "Максимум страниц",
            self.variables.max_pages,
            placeholder="5",
        )
        pages_field.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        items_field = LabeledComboBox(
            panel,
            "Вакансий на странице",
            self.variables.items_on_page,
            ITEMS_ON_PAGE_OPTIONS,
        )
        items_field.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 13))

        output_field = LabeledEntry(
            panel,
            "Файл результата",
            self.variables.output_file,
            placeholder="vacancies",
            suffix=".csv",
        )
        output_field.grid(row=4, column=0, sticky="ew", padx=22)

        start_button = ctk.CTkButton(
            panel,
            text="Начать поиск",
            command=self._handle_primary_action,
            height=48,
            fg_color=COLORS.accent,
            hover_color=COLORS.accent_hover,
            text_color=COLORS.text,
            corner_radius=CONTROL_RADIUS,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
        )
        start_button.grid(
            row=7,
            column=0,
            sticky="sew",
            padx=22,
            pady=(20, 22),
        )

        return FormWidgets(
            query=query_field,
            salary=salary_field,
            pages=pages_field,
            items=items_field,
            output=output_field,
            start_button=start_button,
        )

    def _build_activity_panel(self, workspace: ctk.CTkFrame) -> ActivityWidgets:
        panel = self._panel(workspace)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        activity_header = ctk.CTkFrame(panel, fg_color="transparent")
        activity_header.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 12))
        activity_header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            activity_header,
            text="Ход выполнения",
            anchor="w",
            text_color=COLORS.text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        clear_button = ctk.CTkButton(
            activity_header,
            text="Очистить журнал",
            command=self._clear_log,
            width=142,
            height=34,
            fg_color="transparent",
            hover_color=COLORS.surface_hover,
            border_color=COLORS.border,
            border_width=1,
            text_color=COLORS.text_muted,
            corner_radius=CONTROL_RADIUS,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            state="disabled",
        )
        clear_button.grid(row=0, column=1, sticky="e")

        log_container = ctk.CTkFrame(panel, fg_color="transparent")
        log_container.grid(row=1, column=0, sticky="nsew", padx=22)
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)

        log = ctk.CTkTextbox(
            log_container,
            wrap="word",
            fg_color=COLORS.field,
            border_color=COLORS.border,
            border_width=1,
            text_color=COLORS.text_muted,
            scrollbar_button_color=COLORS.border,
            scrollbar_button_hover_color=COLORS.border_focus,
            corner_radius=CONTROL_RADIUS,
            font=ctk.CTkFont(family=MONOSPACE_FONT_FAMILY, size=12),
            spacing1=3,
            spacing3=3,
        )
        log.grid(row=0, column=0, sticky="nsew")
        log.configure(state="disabled")

        empty_state = ctk.CTkFrame(
            log_container,
            fg_color=COLORS.field,
            border_color=COLORS.border,
            border_width=1,
            corner_radius=CONTROL_RADIUS,
        )
        empty_state.grid(row=0, column=0, sticky="nsew")
        empty_state.columnconfigure(0, weight=1)
        empty_state.rowconfigure((0, 3), weight=1)
        empty_icon = ctk.CTkFrame(
            empty_state,
            width=58,
            height=58,
            fg_color="transparent",
            border_color=COLORS.border_focus,
            border_width=1,
            corner_radius=14,
        )
        empty_icon.grid(row=1, column=0, pady=(0, 14))
        empty_icon.grid_propagate(False)
        ctk.CTkLabel(
            empty_icon,
            text="CSV",
            text_color=COLORS.text_faint,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        ).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(
            empty_state,
            textvariable=self.variables.empty_title,
            text_color=COLORS.text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
        ).grid(row=2, column=0)
        ctk.CTkLabel(
            empty_state,
            textvariable=self.variables.empty_description,
            text_color=COLORS.text_faint,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        ).grid(row=3, column=0, sticky="n", pady=(8, 0))

        progress = ctk.CTkProgressBar(
            panel,
            height=5,
            corner_radius=3,
            fg_color=COLORS.field,
            progress_color=COLORS.accent,
            mode="indeterminate",
        )
        progress.grid(row=2, column=0, sticky="ew", padx=22, pady=(15, 20))
        progress.set(0)

        return ActivityWidgets(
            clear_button=clear_button,
            log=log,
            empty_state=empty_state,
            progress=progress,
        )

    def _build_status_bar(self) -> ctk.CTkLabel:
        status_bar = ctk.CTkFrame(
            self.root,
            height=42,
            fg_color=COLORS.surface,
            corner_radius=0,
            border_width=0,
        )
        status_bar.grid(row=2, column=0, sticky="ew")
        status_bar.grid_propagate(False)
        status_bar.columnconfigure(1, weight=1)

        status_dot = ctk.CTkLabel(
            status_bar,
            text="●",
            width=18,
            text_color=COLORS.success,
            font=ctk.CTkFont(size=17),
        )
        status_dot.grid(row=0, column=0, sticky="e", padx=(20, 5), pady=9)
        ctk.CTkLabel(
            status_bar,
            textvariable=self.variables.status,
            anchor="w",
            text_color=COLORS.text_muted,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        ).grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=9)
        return status_dot

    def _handle_primary_action(self) -> None:
        if self.controller.is_running:
            self._request_stop()
            return
        self._start_search()

    def _start_search(self) -> None:
        variables = self.variables
        try:
            config = build_gui_config(
                query=variables.search_query.get(),
                salary_text=variables.salary.get(),
                max_pages_text=variables.max_pages.get(),
                output_file_text=variables.output_file.get(),
                items_on_page_text=variables.items_on_page.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Проверьте параметры", str(exc), parent=self.root)
            return

        self._clear_log()
        self._set_running(True)
        self._add_status("Запускаю браузер…")
        if not self.controller.start(config):
            self._set_running(True)

    def _request_stop(self) -> None:
        form = self.widgets.form
        self.controller.request_stop()
        self.variables.status.set("Останавливаю поиск…")
        self.widgets.status_dot.configure(text_color=COLORS.danger)
        form.start_button.configure(state="disabled", text="Останавливаю…")
        self._add_status("Получена команда остановки. Завершаю текущую операцию…")

    def _process_events(self) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event)

        self._event_job = self.root.after(100, self._process_events)

    def _handle_event(self, event: ParserEvent) -> None:
        if event.kind is ParserEventType.STATUS:
            self._add_status(event.message)
            return

        self._add_status(event.message)
        self._set_running(False)

        if event.kind is ParserEventType.DONE:
            self.variables.status.set(event.message)
            messagebox.showinfo("Поиск завершён", event.message, parent=self.root)
        elif event.kind is ParserEventType.STOPPED:
            self.variables.status.set(event.message)
            messagebox.showinfo("Поиск остановлен", event.message, parent=self.root)
        else:
            self.variables.status.set("Не удалось завершить поиск")
            self.widgets.status_dot.configure(text_color=COLORS.danger)
            messagebox.showerror(
                "Ошибка поиска",
                "Произошла ошибка. Подробности сохранены в журнале.",
                parent=self.root,
            )

    def _add_status(self, message: str) -> None:
        activity = self.widgets.activity
        clean_message = message.strip()
        self.variables.status.set(clean_message or "Выполняю поиск…")
        if not self._has_log_content:
            activity.empty_state.grid_remove()
            self._has_log_content = True
            activity.clear_button.configure(state="normal")
        activity.log.configure(state="normal")
        activity.log.insert("end", f"{message}\n")
        activity.log.see("end")
        activity.log.configure(state="disabled")

    def _clear_log(self) -> None:
        activity = self.widgets.activity
        activity.log.configure(state="normal")
        activity.log.delete("1.0", "end")
        activity.log.configure(state="disabled")
        self._has_log_content = False
        self.variables.empty_title.set("Журнал пуст")
        self.variables.empty_description.set("Новые события появятся здесь")
        activity.clear_button.configure(state="disabled")
        activity.empty_state.grid()

    def _set_running(self, is_running: bool) -> None:
        form = self.widgets.form
        activity = self.widgets.activity
        for field in form.fields:
            field.set_enabled(not is_running)

        if is_running:
            activity.progress.grid()
            activity.progress.start()
            self.widgets.status_dot.configure(text_color=COLORS.accent)
            form.start_button.configure(
                state="normal",
                text="Остановить поиск",
                fg_color="transparent",
                hover_color=COLORS.surface_hover,
                border_color=COLORS.danger,
                border_width=1,
                text_color=COLORS.danger,
            )
            return

        activity.progress.stop()
        activity.progress.set(0)
        activity.progress.grid_remove()
        self.widgets.status_dot.configure(text_color=COLORS.success)
        form.start_button.configure(
            state="normal",
            text="Начать поиск",
            fg_color=COLORS.accent,
            hover_color=COLORS.accent_hover,
            border_width=0,
            text_color=COLORS.text,
        )

    def close(self) -> None:
        if self.controller.is_running:
            self.controller.request_stop()
        if self._event_job is not None:
            self.root.after_cancel(self._event_job)
            self._event_job = None
        self.root.destroy()


def main() -> None:
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    ParserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
