import queue
import threading
import traceback
import tkinter as tk
from tkinter import messagebox, ttk

from app.core.config import Settings, settings
from app.gui_config import (
    ITEMS_ON_PAGE_OPTIONS,
    build_gui_config,
    output_name_without_csv,
)
from app.hh_parser import build_driver, collect_vacancies, save_to_csv


class ParserApp:
    def __init__(self, root: tk.Tk) -> None:
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
        self.root.geometry("720x620")
        self.root.minsize(620, 520)

        self._build_layout()
        self.root.after(100, self._process_events)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        form = ttk.Frame(self.root, padding=16)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Поисковый запрос").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=(0, 10),
        )
        ttk.Entry(form, textvariable=self.search_query).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 10),
        )

        ttk.Label(form, text="Зарплата от, руб.").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
        )
        ttk.Entry(form, textvariable=self.salary, width=18).grid(
            row=1,
            column=1,
            sticky="w",
        )

        ttk.Label(form, text="Страниц максимум").grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=(10, 0),
        )
        ttk.Entry(form, textvariable=self.max_pages, width=18).grid(
            row=2,
            column=1,
            sticky="w",
            pady=(10, 0),
        )

        ttk.Label(form, text="Имя файла").grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=(10, 0),
        )
        ttk.Entry(form, textvariable=self.output_file).grid(
            row=3,
            column=1,
            sticky="ew",
            pady=(10, 0),
        )

        ttk.Label(form, text="Вакансий на странице").grid(
            row=4,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=(10, 0),
        )
        ttk.Combobox(
            form,
            textvariable=self.items_on_page,
            values=ITEMS_ON_PAGE_OPTIONS,
            state="readonly",
            width=15,
        ).grid(
            row=4,
            column=1,
            sticky="w",
            pady=(10, 0),
        )

        self.start_button = ttk.Button(
            form,
            text="Начать поиск",
            command=self.start_search,
        )
        self.start_button.grid(row=5, column=0, columnspan=2, sticky="w", pady=(16, 0))

        log_frame = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log = tk.Text(log_frame, height=14, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scrollbar.set)

        status_bar = ttk.Label(
            self.root,
            textvariable=self.status,
            anchor="w",
            padding=(16, 8),
        )
        status_bar.grid(row=2, column=0, sticky="ew")

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
            messagebox.showerror("Ошибка", str(exc))
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
                messagebox.showinfo("Готово", message)
            elif event == "error":
                self._add_status(message)
                self.status.set("Ошибка во время поиска")
                self._set_running(False)
                messagebox.showerror("Ошибка", message)

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
        state = "disabled" if is_running else "normal"
        self.start_button.configure(state=state)


def main() -> None:
    root = tk.Tk()
    ParserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
