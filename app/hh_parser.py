import csv
import random
import time
from collections.abc import Callable
from urllib.parse import urlencode

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.core.config import Settings, settings
from app.core.utils import (
    SearchableElement,
    all_texts,
    clean_url,
    first_text,
    normalize_text,
    safe_attr,
    safe_text,
)
from app.schemas import Vacancy

SEARCH_CARD_SELECTORS = (
    "[data-qa='vacancy-serp__vacancy']",
    "[data-qa='vacancy-serp__vacancy-info']",
    "[class*='vacancy-card']",
)
TITLE_SELECTOR = "[data-qa='serp-item__title']"
COMPANY_SELECTORS = (
    "[data-qa='vacancy-serp__vacancy-employer-text']",
    "[data-qa='vacancy-serp__vacancy-employer']",
)
DESCRIPTION_SELECTORS = ("[data-qa='vacancy-description']",)
SKILL_SELECTORS = ("[data-qa='skills-element']",)
StatusCallback = Callable[[str], None]


def emit_status(message: str, on_status: StatusCallback | None = None) -> None:
    print(message)
    if on_status is not None:
        on_status(message)


def build_search_url(page: int, config: Settings = settings) -> str:
    params = {
        "text": config.search_query,
        "excluded_text": "",
        "salary": config.salary,
        "area": config.area,
        "currency_code": config.currency_code,
        "experience": config.experience,
        "order_by": config.order_by,
        "search_period": config.search_period,
        "items_on_page": config.items_on_page,
        "L_save_area": "true",
        "hhtmFrom": "vacancy_search_filter",
        "page": page,
    }
    return f"{config.base_search_url}?{urlencode(params)}"


def build_driver(config: Settings = settings) -> ChromeDriver:
    options = Options()
    options.page_load_strategy = config.page_load_strategy
    if config.headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-sync")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if config.disable_images:
        options.add_experimental_option(
            "prefs",
            {"profile.managed_default_content_settings.images": 2},
        )
    options.add_argument(f"user-agent={config.user_agent}")

    if config.chromedriver_path:
        service = Service(config.chromedriver_path)
        return ChromeDriver(service=service, options=options)
    return ChromeDriver(options=options)


def parse_card(card: SearchableElement) -> Vacancy:
    title = safe_text(card, TITLE_SELECTOR, default="")
    href = safe_attr(card, TITLE_SELECTOR, "href")
    if not title:
        title = normalize_text(card.text) or "—"
    if not href:
        href = card.get_attribute("href") or ""
    company = first_text(card, COMPANY_SELECTORS)
    return Vacancy(title=title, company=company, url=clean_url(href))


def find_search_cards(driver: ChromeDriver) -> list[SearchableElement]:
    for selector in SEARCH_CARD_SELECTORS:
        cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if cards:
            return cards

    title_links = driver.find_elements(By.CSS_SELECTOR, TITLE_SELECTOR)
    cards: list[SearchableElement] = []
    for title_link in title_links:
        try:
            cards.append(
                title_link.find_element(
                    By.XPATH,
                    (
                        "./ancestor::*[.//*[@data-qa='serp-item__title'] "
                        "and (.//*[@data-qa='vacancy-serp__vacancy-employer-text'] "
                        "or .//*[@data-qa='vacancy-serp__vacancy-employer'])][1]"
                    ),
                )
            )
        except NoSuchElementException:
            cards.append(title_link)
    return cards


def wait_for_search_cards(
    driver: ChromeDriver,
    expected_count: int,
    timeout: float,
) -> None:
    if timeout <= 0:
        return

    try:
        WebDriverWait(driver, timeout).until(
            lambda current_driver: len(find_search_cards(current_driver))
            >= expected_count
        )
    except TimeoutException:
        return


def parse_vacancy_details(
    driver: ChromeDriver,
    vacancy: Vacancy,
    config: Settings = settings,
    on_status: StatusCallback | None = None,
) -> Vacancy:
    if vacancy.url == "—":
        return vacancy

    emit_status(f"  -> Открываю вакансию: {vacancy.title}", on_status)
    driver.get(vacancy.url)
    try:
        WebDriverWait(driver, config.page_timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
    except TimeoutException:
        return vacancy

    description = first_text(driver, DESCRIPTION_SELECTORS)
    key_skills = all_texts(driver, SKILL_SELECTORS)

    return vacancy.model_copy(
        update={
            "description": description,
            "key_skills": key_skills,
        }
    )


def parse_search_page(
    driver: ChromeDriver,
    page: int,
    config: Settings = settings,
    on_status: StatusCallback | None = None,
) -> tuple[list[Vacancy], bool]:
    url = build_search_url(page, config)
    emit_status(f"  -> Загрузка страницы {page}: {url}", on_status)
    driver.get(url)

    try:
        WebDriverWait(driver, config.page_timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_SELECTOR))
        )
    except TimeoutException:
        emit_status(
            f"  x Ссылки вакансий не появились на странице {page}. Завершаем.",
            on_status,
        )
        emit_status(f"  Текущий URL браузера: {driver.current_url}", on_status)
        return [], False

    wait_for_search_cards(
        driver, config.items_on_page, config.search_cards_wait_timeout
    )
    cards = find_search_cards(driver)
    vacancies = [vacancy for card in cards if (vacancy := parse_card(card)).url != "—"]
    has_next = bool(driver.find_elements(By.CSS_SELECTOR, "[data-qa='pager-next']"))
    emit_status(
        f"  + Собрано вакансий: {len(vacancies)} | Следующая страница: {has_next}",
        on_status,
    )
    return vacancies, has_next


def collect_vacancies(
    driver: ChromeDriver,
    config: Settings = settings,
    on_status: StatusCallback | None = None,
) -> list[Vacancy]:
    vacancies: list[Vacancy] = []
    for page in range(config.max_pages):
        page_vacancies, has_next = parse_search_page(driver, page, config, on_status)
        for vacancy in page_vacancies:
            enriched = parse_vacancy_details(driver, vacancy, config, on_status)
            vacancies.append(enriched)

            delay = random.uniform(config.delay_min, config.delay_max)
            emit_status(
                f"  Пауза перед следующей вакансией: {delay:.1f} сек.", on_status
            )
            time.sleep(delay)

        if not has_next:
            emit_status(
                f"\n  Следующей страницы нет — сбор завершён на странице {page}.",
                on_status,
            )
            break

        delay = random.uniform(config.delay_min, config.delay_max)
        emit_status(f"  Пауза перед следующей страницей: {delay:.1f} сек.", on_status)
        time.sleep(delay)
    return vacancies


def save_to_csv(
    vacancies: list[Vacancy],
    filename: str,
    on_status: StatusCallback | None = None,
) -> None:
    field_names = [
        "Вакансия",
        "Компания",
        "Ссылка",
        "Описание вакансии",
        "Ключевые навыки",
    ]
    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(field_names)
        for vacancy in vacancies:
            writer.writerow(
                [
                    vacancy.title,
                    vacancy.company,
                    vacancy.url,
                    vacancy.description,
                    vacancy.key_skills_text,
                ]
            )
    emit_status(
        f"\nРезультаты сохранены в «{filename}» ({len(vacancies)} вакансий)",
        on_status,
    )


def print_table(vacancies: list[Vacancy]) -> None:
    col_title = min(max((len(v.title) for v in vacancies), default=30), 60)
    col_company = min(max((len(v.company) for v in vacancies), default=20), 40)

    sep = f"+{'-' * (col_title + 2)}+{'-' * (col_company + 2)}+{'-' * 55}+"
    header = (
        f"| {'Вакансия':<{col_title}} "
        f"| {'Компания':<{col_company}} "
        f"| {'Ссылка':<53} |"
    )
    print(sep)
    print(header)
    print(sep)
    for vacancy in vacancies:
        print(
            f"| {vacancy.title[:col_title]:<{col_title}} "
            f"| {vacancy.company[:col_company]:<{col_company}} "
            f"| {vacancy.url[:53]:<53} |"
        )
    print(sep)
