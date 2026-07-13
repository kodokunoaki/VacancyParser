import queue
from unittest.mock import Mock, patch

from app.core.config import Settings
from app.gui_controller import ParserController
from app.schemas import ParserEvent, ParserEventType, Vacancy


def event_messages(events: queue.Queue[ParserEvent]) -> list[ParserEvent]:
    result: list[ParserEvent] = []
    while not events.empty():
        result.append(events.get_nowait())
    return result


@patch("app.gui_controller.save_to_csv")
@patch("app.gui_controller.collect_vacancies")
@patch("app.gui_controller.build_driver")
def test_controller_publishes_done_and_closes_driver(
    build_driver_mock: Mock,
    collect_vacancies_mock: Mock,
    save_to_csv_mock: Mock,
) -> None:
    driver = build_driver_mock.return_value
    vacancy = Vacancy(
        title="Python-разработчик",
        company="Компания",
        url="https://hh.ru/vacancy/1",
    )
    collect_vacancies_mock.return_value = [vacancy]
    events: queue.Queue[ParserEvent] = queue.Queue()
    controller = ParserController(events)
    config = Settings(output_file="python.csv")

    assert controller.start(config) is True
    assert controller.wait(timeout=1) is True

    save_to_csv_mock.assert_called_once()
    driver.quit.assert_called_once_with()
    published = event_messages(events)
    assert published[-1].kind is ParserEventType.DONE
    assert "1 вакансий" in published[-1].message
    assert "python.csv" in published[-1].message


@patch("app.gui_controller.save_to_csv")
@patch("app.gui_controller.collect_vacancies")
@patch("app.gui_controller.build_driver")
def test_controller_saves_partial_result_after_stop(
    build_driver_mock: Mock,
    collect_vacancies_mock: Mock,
    save_to_csv_mock: Mock,
) -> None:
    vacancy = Vacancy(
        title="Python-разработчик",
        company="Компания",
        url="https://hh.ru/vacancy/1",
    )
    events: queue.Queue[ParserEvent] = queue.Queue()
    controller = ParserController(events)
    collect_vacancies_mock.side_effect = lambda *_args: (
        controller.request_stop(),
        [vacancy],
    )[1]

    assert controller.start(Settings(output_file="partial.csv")) is True
    assert controller.wait(timeout=1) is True

    save_to_csv_mock.assert_called_once()
    build_driver_mock.return_value.quit.assert_called_once_with()
    published = event_messages(events)
    assert published[-1].kind is ParserEventType.STOPPED
    assert "partial.csv" in published[-1].message


@patch("app.gui_controller.build_driver", side_effect=RuntimeError("driver failed"))
def test_controller_publishes_traceback_on_error(build_driver_mock: Mock) -> None:
    events: queue.Queue[ParserEvent] = queue.Queue()
    controller = ParserController(events)

    assert controller.start(Settings()) is True
    assert controller.wait(timeout=1) is True

    build_driver_mock.assert_called_once()
    published = event_messages(events)
    assert published[-1].kind is ParserEventType.ERROR
    assert "RuntimeError: driver failed" in published[-1].message
