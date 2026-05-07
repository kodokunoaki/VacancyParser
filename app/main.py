from app.core.config import settings
from app.hh_parser import build_driver, collect_vacancies, print_table, save_to_csv


def main() -> None:
    print("=" * 60)
    print("  Парсер вакансий hh.ru")
    print("=" * 60)

    driver = build_driver(settings)
    try:
        vacancies = collect_vacancies(driver, settings)
    finally:
        driver.quit()

    if not vacancies:
        print("\nВакансии не найдены. Проверьте URL или селекторы.")
        return

    print_table(vacancies)
    save_to_csv(vacancies, settings.output_file)


if __name__ == "__main__":
    main()
