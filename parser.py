"""
Парсер вакансий с hh.ru с использованием Selenium.
Собирает: Наименование вакансии | Название компании | Ссылка на вакансию
"""
 
import time
import csv
import random
from dataclasses import dataclass
 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException 
 
# ──────────────────────────────────────────────
# Конфигурация
# ──────────────────────────────────────────────
BASE_URL = (
    "https://hh.ru/search/vacancy"
    "?text=Руководитель+отдела+маркетинга"
    "&excluded_text="
    "&salary=150000"
    "&currency_code=RUR"
    "&experience=doesNotMatter"
    "&order_by=relevance"
    "&search_period=0"
    "&items_on_page=100"
    "&L_save_area=true"
    "&hhtmFrom=vacancy_search_filter"
    "&page={page}"
)
 
MAX_PAGES   = 5          # максимальное число страниц для обхода
OUTPUT_FILE = "vacancies.csv"
DELAY_MIN   = 2.0         # минимальная пауза между страницами (сек)
DELAY_MAX   = 4.5         # максимальная пауза между страницами (сек)
PAGE_TIMEOUT = 30         # таймаут ожидания элементов (сек)
 
 
# ──────────────────────────────────────────────
# Модель данных
# ──────────────────────────────────────────────
@dataclass
class Vacancy:
    title:   str
    company: str
    url:     str
 
 
# ──────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────
def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # Системный chromedriver, который идёт в паре с chromium-browser
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)
 
 
def safe_text(element, selector: str, default: str = "—") -> str:
    """Безопасно извлекает текст вложенного элемента."""
    try:
        return element.find_element(By.CSS_SELECTOR, selector).text.strip()
    except NoSuchElementException:
        return default
 
 
def safe_attr(element, selector: str, attr: str, default: str = "") -> str:
    """Безопасно извлекает атрибут вложенного элемента."""
    try:
        return element.find_element(By.CSS_SELECTOR, selector).get_attribute(attr) or default
    except NoSuchElementException:
        return default
 
 
# ──────────────────────────────────────────────
# Основная логика парсинга
# ──────────────────────────────────────────────
def parse_page(driver: webdriver.Chrome, page: int) -> tuple[list[Vacancy], bool]:
    """
    Загружает одну страницу результатов и возвращает
    (список вакансий, есть_ли_следующая_страница).
    """
    url = BASE_URL.format(page=page)
    print(f"  → Загрузка страницы {page}: {url}")
    driver.get(url)
 
    # Ждём появления карточек вакансий
    try:
        WebDriverWait(driver, PAGE_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-qa='vacancy-serp__vacancy']")
            )
        )
    except TimeoutException:
        print(f"  ✗ Карточки вакансий не появились на странице {page}. Завершаем.")
        return [], False
 
    cards = driver.find_elements(By.CSS_SELECTOR, "[data-qa='vacancy-serp__vacancy']")
    vacancies: list[Vacancy] = []
 
    for card in cards:
        # Название вакансии + ссылка
        title = safe_text(card, "[data-qa='serp-item__title']")
        href  = safe_attr(card, "[data-qa='serp-item__title']", "href")
 
        # Убираем UTM-хвост (оставляем чистую ссылку до «?»)
        clean_url = href.split("?")[0] if href else "—"
 
        # Название компании
        company = safe_text(card, "[data-qa='vacancy-serp__vacancy-employer-text']")
        if company == "—":
            company = safe_text(card, "[data-qa='vacancy-serp__vacancy-employer']")
 
        vacancies.append(Vacancy(title=title, company=company, url=clean_url))
 
    # Проверяем наличие кнопки «следующая страница»
    has_next = bool(
        driver.find_elements(By.CSS_SELECTOR, "[data-qa='pager-next']")
    )
    print(f"  ✓ Собрано вакансий: {len(vacancies)} | Следующая страница: {has_next}")
    return vacancies, has_next
 
 
def save_to_csv(vacancies: list[Vacancy], filename: str) -> None:
    """Сохраняет список вакансий в CSV-файл."""
    field_names = ["Наименование вакансии", "Название компании", "Ссылка на вакансию"]
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(field_names)
        for v in vacancies:
            writer.writerow([v.title, v.company, v.url])
    print(f"\n💾 Результаты сохранены в «{filename}» ({len(vacancies)} вакансий)")
 
 
def print_table(vacancies: list[Vacancy]) -> None:
    """Выводит вакансии в консоль в виде таблицы."""
    col_title   = max(len(v.title)   for v in vacancies) if vacancies else 30
    col_company = max(len(v.company) for v in vacancies) if vacancies else 20
    col_title   = min(col_title,   60)
    col_company = min(col_company, 40)
 
    sep = f"+{'-'*(col_title+2)}+{'-'*(col_company+2)}+{'-'*55}+"
    header = (
        f"| {'Наименование вакансии':<{col_title}} "
        f"| {'Название компании':<{col_company}} "
        f"| {'Ссылка на вакансию':<53} |"
    )
    print(sep)
    print(header)
    print(sep)
    for v in vacancies:
        title   = v.title[:col_title]
        company = v.company[:col_company]
        url     = v.url[:53]
        print(
            f"| {title:<{col_title}} "
            f"| {company:<{col_company}} "
            f"| {url:<53} |"
        )
    print(sep)
 
 
# ──────────────────────────────────────────────
# Точка входа
# ──────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  Парсер вакансий hh.ru")
    print("=" * 60)
 
    driver = build_driver()
    all_vacancies: list[Vacancy] = []
 
    try:
        for page in range(MAX_PAGES):
            vacancies, has_next = parse_page(driver, page)
            all_vacancies.extend(vacancies)
 
            if not has_next:
                print(f"\n  Следующей страницы нет — сбор завершён на странице {page}.")
                break
 
            # Вежливая пауза между запросами
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            print(f"  ⏳ Пауза {delay:.1f} сек…")
            time.sleep(delay)
    finally:
        driver.quit()
 
    if not all_vacancies:
        print("\n⚠️  Вакансии не найдены. Проверьте URL или селекторы.")
        return
 
    print_table(all_vacancies)
    save_to_csv(all_vacancies, OUTPUT_FILE)
 
 
if __name__ == "__main__":
    main()
