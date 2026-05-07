from app.core.config import Settings, settings

ITEMS_ON_PAGE_OPTIONS = ("20", "50", "100")


def output_name_without_csv(filename: str) -> str:
    name = filename.strip()
    if name.lower().endswith(".csv"):
        return name[:-4]
    return name


def csv_filename_from_input(filename: str) -> str:
    name = output_name_without_csv(filename)
    if not name:
        raise ValueError("Введите имя файла.")
    return f"{name}.csv"


def build_gui_config(
    query: str,
    salary_text: str,
    max_pages_text: str,
    output_file_text: str,
    items_on_page_text: str,
    base_settings: Settings = settings,
) -> Settings:
    search_query = query.strip()
    if not search_query:
        raise ValueError("Введите поисковый запрос.")

    try:
        salary = int(salary_text.strip())
    except ValueError as exc:
        raise ValueError("Зарплата должна быть целым числом.") from exc

    if salary < 0:
        raise ValueError("Зарплата не может быть отрицательной.")

    try:
        max_pages = int(max_pages_text.strip())
    except ValueError as exc:
        raise ValueError("Количество страниц должно быть целым числом.") from exc

    if max_pages <= 0:
        raise ValueError("Количество страниц должно быть больше нуля.")

    try:
        items_on_page = int(items_on_page_text.strip())
    except ValueError as exc:
        raise ValueError("Выберите количество вакансий на странице.") from exc

    if str(items_on_page) not in ITEMS_ON_PAGE_OPTIONS:
        raise ValueError("Выберите количество вакансий на странице: 20, 50 или 100.")

    return base_settings.model_copy(
        update={
            "search_query": search_query,
            "salary": salary,
            "max_pages": max_pages,
            "output_file": csv_filename_from_input(output_file_text),
            "items_on_page": items_on_page,
        }
    )
