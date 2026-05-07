from unittest.mock import Mock, patch

from selenium.common.exceptions import NoSuchElementException

from app.core.config import Settings
from app.core.utils import clean_url, first_text
from app.gui_config import (
    build_gui_config,
    csv_filename_from_input,
    output_name_without_csv,
)
from app.hh_parser import (
    build_driver,
    build_search_url,
    find_search_cards,
    parse_card,
    parse_vacancy_details,
    wait_for_search_cards,
)
from app.schemas import Vacancy


class FakeElement:
    def __init__(
        self,
        text: str = "",
        attrs: dict[str, str] | None = None,
        children: dict[str, "FakeElement"] | None = None,
        groups: dict[str, list["FakeElement"]] | None = None,
    ) -> None:
        self.text = text
        self._attrs = attrs or {}
        self._children = children or {}
        self._groups = groups or {}

    def find_element(self, by: str, value: str) -> "FakeElement":
        if value not in self._children:
            raise NoSuchElementException(value)
        return self._children[value]

    def find_elements(self, by: str, value: str) -> list["FakeElement"]:
        return self._groups.get(value, [])

    def get_attribute(self, name: str) -> str | None:
        return self._attrs.get(name)


def test_clean_url_removes_query_and_fragment() -> None:
    url = "https://hh.ru/vacancy/132448794?from=search#anchor"

    assert clean_url(url) == "https://hh.ru/vacancy/132448794"


def test_first_text_returns_first_existing_selector() -> None:
    element = FakeElement(
        children={
            "[data-qa='second']": FakeElement("  Компания   мечты  "),
        }
    )

    assert first_text(element, ["[data-qa='first']", "[data-qa='second']"]) == (
        "Компания мечты"
    )


def test_build_search_url_uses_settings() -> None:
    config = Settings(search_query="Python developer", max_pages=1)

    url = build_search_url(page=2, config=config)

    assert "text=Python+developer" in url
    assert "salary=150000" in url
    assert "page=2" in url


def test_output_name_without_csv_removes_suffix() -> None:
    assert output_name_without_csv(" vacancies.CSV ") == "vacancies"


def test_csv_filename_from_input_adds_csv_suffix() -> None:
    assert csv_filename_from_input("result") == "result.csv"
    assert csv_filename_from_input("result.csv") == "result.csv"


def test_build_gui_config_uses_form_values() -> None:
    config = build_gui_config(
        query=" Python developer ",
        salary_text="200000",
        max_pages_text="3",
        output_file_text="python_jobs",
        items_on_page_text="50",
        base_settings=Settings(),
    )

    assert config.search_query == "Python developer"
    assert config.salary == 200000
    assert config.max_pages == 3
    assert config.output_file == "python_jobs.csv"
    assert config.items_on_page == 50


def test_build_gui_config_rejects_invalid_items_on_page() -> None:
    try:
        build_gui_config(
            query="Python",
            salary_text="100000",
            max_pages_text="1",
            output_file_text="result",
            items_on_page_text="30",
            base_settings=Settings(),
        )
    except ValueError as exc:
        assert "20, 50 или 100" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid items_on_page")


@patch("app.hh_parser.ChromeDriver")
def test_build_driver_uses_selenium_manager_without_chromedriver_path(
    chrome_mock: Mock,
) -> None:
    config = Settings(chromedriver_path=None)

    build_driver(config)

    _, kwargs = chrome_mock.call_args
    assert "options" in kwargs
    assert "service" not in kwargs


@patch("app.hh_parser.ChromeDriver")
def test_build_driver_configures_fast_page_loading(chrome_mock: Mock) -> None:
    config = Settings(page_load_strategy="eager", disable_images=True)

    build_driver(config)

    _, kwargs = chrome_mock.call_args
    options = kwargs["options"]
    assert options.page_load_strategy == "eager"
    assert options.experimental_options["prefs"] == {
        "profile.managed_default_content_settings.images": 2
    }


@patch("app.hh_parser.ChromeDriver")
def test_build_driver_allows_images_when_configured(chrome_mock: Mock) -> None:
    config = Settings(disable_images=False)

    build_driver(config)

    _, kwargs = chrome_mock.call_args
    assert "prefs" not in kwargs["options"].experimental_options


@patch("app.hh_parser.ChromeDriver")
@patch("app.hh_parser.Service")
def test_build_driver_uses_service_with_chromedriver_path(
    service_mock: Mock,
    chrome_mock: Mock,
) -> None:
    config = Settings(chromedriver_path="C:/tools/chromedriver.exe")

    build_driver(config)

    service_mock.assert_called_once_with("C:/tools/chromedriver.exe")
    _, kwargs = chrome_mock.call_args
    assert kwargs["service"] == service_mock.return_value
    assert "options" in kwargs


def test_parse_card_returns_vacancy_from_search_card() -> None:
    card = FakeElement(
        children={
            "[data-qa='serp-item__title']": FakeElement(
                "Маркетолог",
                attrs={"href": "https://hh.ru/vacancy/1?query=marketing"},
            ),
            "[data-qa='vacancy-serp__vacancy-employer-text']": FakeElement(
                "ООО Ромашка"
            ),
        }
    )

    vacancy = parse_card(card)

    assert vacancy == Vacancy(
        title="Маркетолог",
        company="ООО Ромашка",
        url="https://hh.ru/vacancy/1",
    )


def test_parse_card_returns_vacancy_from_title_link_fallback() -> None:
    title_link = FakeElement(
        "Маркетолог",
        attrs={"href": "https://hh.ru/vacancy/1?query=marketing"},
    )

    vacancy = parse_card(title_link)

    assert vacancy == Vacancy(
        title="Маркетолог",
        company="—",
        url="https://hh.ru/vacancy/1",
    )


def test_find_search_cards_falls_back_to_title_links() -> None:
    title_link = FakeElement(
        "Маркетолог",
        attrs={"href": "https://hh.ru/vacancy/1"},
    )
    driver = FakeElement(
        groups={
            "[data-qa='serp-item__title']": [title_link],
        }
    )

    assert find_search_cards(driver) == [title_link]


@patch("app.hh_parser.WebDriverWait")
def test_wait_for_search_cards_waits_until_expected_count(wait_mock: Mock) -> None:
    driver = FakeElement(
        groups={
            "[data-qa='vacancy-serp__vacancy']": [
                FakeElement("Маркетолог") for _ in range(20)
            ],
        }
    )

    wait_for_search_cards(driver, expected_count=20, timeout=5.0)

    condition = wait_mock.return_value.until.call_args.args[0]
    wait_mock.assert_called_once_with(driver, 5.0)
    assert condition(driver) is True


@patch("app.hh_parser.WebDriverWait")
def test_parse_vacancy_details_enriches_vacancy(wait_mock: Mock) -> None:
    wait_mock.return_value.until.return_value = True
    driver = FakeElement(
        groups={
            "[data-qa='skills-element']": [
                FakeElement("SEO"),
                FakeElement("Аналитика"),
            ],
        },
        children={
            "[data-qa='vacancy-description']": FakeElement(
                "  Делать маркетинг  и аналитику "
            ),
        },
    )
    driver.get = Mock()
    vacancy = Vacancy(title="Маркетолог", company="ООО Ромашка", url="https://hh.ru/1")

    enriched = parse_vacancy_details(driver, vacancy)

    driver.get.assert_called_once_with("https://hh.ru/1")
    assert enriched.description == "Делать маркетинг и аналитику"
    assert enriched.key_skills == ["SEO", "Аналитика"]
