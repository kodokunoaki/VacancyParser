import queue
import threading
import traceback
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from app.core.config import Settings, settings
from app.gui_config import (
    ITEMS_ON_PAGE_OPTIONS,
    build_gui_config,
    output_name_without_csv,
)
from app.hh_parser import build_driver, collect_vacancies, save_to_csv


WINDOW_BG = "#0b1020"
PANEL_BG = "#121a2e"
PANEL_SOFT_BG = "#17213a"
FIELD_BG = "#0f1729"
BORDER_COLOR = "#2b3958"
TEXT_COLOR = "#f5f7fb"
MUTED_TEXT_COLOR = "#97a3ba"
ACCENT_COLOR = "#5eead4"
ACCENT_HOVER_COLOR = "#38cfc0"


class ParserApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.search_query = tk.StringVar(value=settings.search_query)
        self.salary = tk.StringVar(value=str(settings.salary))
        self.max_pages = tk.StringVar(value=str(settings.max_pages))
        self.output_file = tk.StringVar(
            value=output_name_without_csv(settings.output_file)
        )
        self.items_on_page = tk.StringVar(value=str(settings.items_on_page))
        self.status = tk.StringVar(value="Готов к поиску")

        self.root.title("HH Parser")
        self.root.geometry("960x640")
        self.root.minsize(780, 640)
        self.root.configure(fg_color=WINDOW_BG)

        self._build_layout()
        self.root.after(100, self._process_events)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        shell = ctk.CTkFrame(
            self.root,
            fg_color=WINDOW_BG,
            corner_radius=0,
        )
        shell.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
        shell.columnconfigure(0, weight=0)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            shell,
            fg_color=PANEL_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=22,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="HH Parser",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 2))
        ctk.CTkLabel(
            header,
            text="Поиск, сбор и экспорт вакансий hh.ru в CSV",
            font=ctk.CTkFont(size=14),
            text_color=MUTED_TEXT_COLOR,
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 18))

        form = ctk.CTkFrame(
            shell,
            width=330,
            fg_color=PANEL_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=22,
        )
        form.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        form.grid_propagate(False)
        form.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form,
            text="Параметры",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 14))

        self._add_entry(
            form,
            row=1,
            label="Поисковый запрос",
            variable=self.search_query,
        )
        self._add_entry(
            form,
            row=2,
            label="Зарплата от, руб.",
            variable=self.salary,
        )
        self._add_entry(
            form,
            row=3,
            label="Страниц максимум",
            variable=self.max_pages,
        )
        self._add_entry(
            form,
            row=4,
            label="Имя файла",
            variable=self.output_file,
        )

        ctk.CTkLabel(
            form,
            text="Вакансий на странице",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=MUTED_TEXT_COLOR,
        ).grid(row=9, column=0, sticky="w", padx=20, pady=(6, 6))
        items_combo = ctk.CTkComboBox(
            form,
            values=list(ITEMS_ON_PAGE_OPTIONS),
            variable=self.items_on_page,
            state="readonly",
            fg_color=FIELD_BG,
            border_color=BORDER_COLOR,
            button_color=PANEL_SOFT_BG,
            button_hover_color=BORDER_COLOR,
            dropdown_fg_color=PANEL_BG,
            dropdown_hover_color=PANEL_SOFT_BG,
            dropdown_text_color=TEXT_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=12,
            height=42,
        )
        items_combo.grid(row=10, column=0, sticky="ew", padx=20, pady=(0, 18))

        self.start_button = ctk.CTkButton(
            form,
            text="Начать поиск",
            command=self.start_search,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER_COLOR,
            text_color="#06111f",
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=14,
            height=46,
        )
        self.start_button.grid(row=11, column=0, sticky="ew", padx=20, pady=(4, 12))

        self.progress = ctk.CTkProgressBar(
            form,
            mode="indeterminate",
            progress_color=ACCENT_COLOR,
            fg_color=FIELD_BG,
            height=8,
            corner_radius=8,
        )
        self.progress.grid(row=12, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.progress.set(0)

        log_panel = ctk.CTkFrame(
            shell,
            fg_color=PANEL_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=22,
        )
        log_panel.grid(row=1, column=1, sticky="nsew")
        log_panel.columnconfigure(0, weight=1)
        log_panel.rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_panel,
            text="Журнал выполнения",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))

        self.log = ctk.CTkTextbox(
            log_panel,
            wrap="word",
            fg_color=FIELD_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=16,
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.log.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.log.configure(state="disabled")

        status_bar = ctk.CTkFrame(
            log_panel,
            fg_color=PANEL_SOFT_BG,
            corner_radius=16,
        )
        status_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        status_bar.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            status_bar,
            textvariable=self.status,
            anchor="w",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=10)

    def _add_entry(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=MUTED_TEXT_COLOR,
        ).grid(row=row * 2 - 1, column=0, sticky="w", padx=20, pady=(0, 6))
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            fg_color=FIELD_BG,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text_color=MUTED_TEXT_COLOR,
            corner_radius=12,
            height=42,
        )
        entry.grid(row=row * 2, column=0, sticky="ew", padx=20, pady=(0, 14))
        return entry

    def start_search(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return

        try:
            config = build_gui_config(
                query=self.search_query.get(),
                salary_text=self.salary.get(),
                max_pages_text=self.max_pages.get(),
                output_file_text=self.output_file.get(),
                items_on_page_text=self.items_on_page.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self.root)
            return

        self._clear_log()
        self._set_running(True)
        self._add_status("Запускаю браузер...")

        self.worker = threading.Thread(
            target=self._run_parser,
            args=(config,),
            daemon=True,
        )
        self.worker.start()

    def _run_parser(self, config: Settings) -> None:
        driver = None
        try:
            driver = build_driver(config)
            vacancies = collect_vacancies(driver, config, self._queue_status)
            if not vacancies:
                self.events.put(("done", "Вакансии не найдены."))
                return

            save_to_csv(vacancies, config.output_file, self._queue_status)
            self.events.put(
                (
                    "done",
                    f"Готово: сохранено {len(vacancies)} вакансий в {config.output_file}",
                )
            )
        except Exception:
            self.events.put(("error", traceback.format_exc()))
        finally:
            if driver is not None:
                driver.quit()

    def _queue_status(self, message: str) -> None:
        self.events.put(("status", message))

    def _process_events(self) -> None:
        while True:
            try:
                event, message = self.events.get_nowait()
            except queue.Empty:
                break

            if event == "status":
                self._add_status(message)
            elif event == "done":
                self._add_status(message)
                self.status.set(message)
                self._set_running(False)
                messagebox.showinfo("Готово", message, parent=self.root)
            elif event == "error":
                self._add_status(message)
                self.status.set("Ошибка во время поиска")
                self._set_running(False)
                messagebox.showerror("Ошибка", message, parent=self.root)

        self.root.after(100, self._process_events)

    def _add_status(self, message: str) -> None:
        self.status.set(message.strip() or "Работаю...")
        self.log.configure(state="normal")
        self.log.insert("end", f"{message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _set_running(self, is_running: bool) -> None:
        if is_running:
            self.start_button.configure(state="disabled", text="Поиск запущен")
            self.progress.start()
            return

        self.start_button.configure(state="normal", text="Начать поиск")
        self.progress.stop()
        self.progress.set(0)


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    ParserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
