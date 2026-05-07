from collections.abc import Iterable
from typing import Protocol
from urllib.parse import urlsplit

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


class SearchableElement(Protocol):
    text: str

    def find_element(self, by: str, value: str) -> "SearchableElement": ...

    def find_elements(self, by: str, value: str) -> list["SearchableElement"]: ...

    def get_attribute(self, name: str) -> str | None: ...


def safe_text(
    element: SearchableElement,
    selector: str,
    default: str = "—",
) -> str:
    try:
        text = element.find_element(By.CSS_SELECTOR, selector).text.strip()
    except NoSuchElementException:
        return default
    return text or default


def safe_attr(
    element: SearchableElement,
    selector: str,
    attr: str,
    default: str = "",
) -> str:
    try:
        value = element.find_element(By.CSS_SELECTOR, selector).get_attribute(attr)
    except NoSuchElementException:
        return default
    return value or default


def first_text(
    element: SearchableElement,
    selectors: Iterable[str],
    default: str = "—",
) -> str:
    for selector in selectors:
        text = safe_text(element, selector, default="")
        if text:
            return normalize_text(text)
    return default


def all_texts(element: SearchableElement, selectors: Iterable[str]) -> list[str]:
    values: list[str] = []
    for selector in selectors:
        for item in element.find_elements(By.CSS_SELECTOR, selector):
            text = normalize_text(item.text)
            if text and text not in values:
                values.append(text)
    return values


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def clean_url(value: str) -> str:
    if not value:
        return "—"
    parts = urlsplit(value)
    return parts._replace(query="", fragment="").geturl()
