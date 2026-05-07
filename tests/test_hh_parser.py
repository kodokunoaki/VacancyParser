from unittest.mock import Mock, patch

from selenium.common.exceptions import NoSuchElementException

from app.core.config import Settings
from app.core.utils import clean_url, first_text
from app.hh_parser import (
    build_search_url,
    find_search_cards,
    parse_card,
    parse_vacancy_details,
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
