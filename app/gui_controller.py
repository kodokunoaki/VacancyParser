import queue
import threading
import traceback

from app.core.config import Settings
from app.hh_parser import build_driver, collect_vacancies, save_to_csv
from app.schemas import ParserEvent, ParserEventType, Vacancy


class ParserController:
    """Runs the parser outside the UI thread and publishes typed events."""

    def __init__(self, events: queue.Queue[ParserEvent]) -> None:
        self.events = events
        self._worker: threading.Thread | None = None
        self._stop_requested = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def start(self, config: Settings) -> bool:
        if self.is_running:
            return False

        self._stop_requested.clear()
        self._worker = threading.Thread(
            target=self._run,
            args=(config,),
            daemon=True,
            name="hh-parser-worker",
        )
        self._worker.start()
        return True

    def request_stop(self) -> None:
        self._stop_requested.set()

    def _publish(self, kind: ParserEventType, message: str) -> None:
        self.events.put(ParserEvent(kind=kind, message=message))

    def _publish_status(self, message: str) -> None:
        self._publish(ParserEventType.STATUS, message)

    def _run(self, config: Settings) -> None:
        driver = None
        try:
            driver = build_driver(config)
            vacancies = collect_vacancies(
                driver,
                config,
                self._publish_status,
                self._stop_requested.is_set,
            )

            if self._stop_requested.is_set():
                self._finish_stopped(vacancies, config.output_file)
                return

            if not vacancies:
                self._publish(ParserEventType.DONE, "Вакансии не найдены.")
                return

            save_to_csv(vacancies, config.output_file, self._publish_status)
            self._publish(
                ParserEventType.DONE,
                (f"Готово: сохранено {len(vacancies)} вакансий в {config.output_file}"),
            )
        except Exception:
            if self._stop_requested.is_set():
                self._publish(
                    ParserEventType.STOPPED,
                    "Остановлено: вакансии не сохранены.",
                )
                return
            self._publish(ParserEventType.ERROR, traceback.format_exc())
        finally:
            if driver is not None:
                driver.quit()

    def _finish_stopped(
        self,
        vacancies: list[Vacancy],
        output_file: str,
    ) -> None:
        if not vacancies:
            self._publish(
                ParserEventType.STOPPED,
                "Остановлено: вакансии не сохранены.",
            )
            return

        save_to_csv(vacancies, output_file, self._publish_status)
        self._publish(
            ParserEventType.STOPPED,
            (f"Остановлено: сохранено {len(vacancies)} вакансий в {output_file}"),
        )
