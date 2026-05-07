# HH Parser
 
Парсер вакансий с [hh.ru](https://hh.ru) на Python с использованием Selenium.  
Собирает вакансии по заданным параметрам поиска, переходит в каждую карточку
и сохраняет описание вакансии и ключевые навыки в CSV.
 
---
 
## Структура проекта
 
```
HHParser/
├── app/
│   ├── __init__.py
│   ├── main.py               # Точка входа
│   ├── hh_parser.py          # Логика сбора и обогащения вакансий
│   ├── schemas.py            # Pydantic-схемы данных
│   └── core/
│       ├── __init__.py
│       ├── config.py         # Настройки приложения (pydantic-settings)
│       └── utils.py          # Вспомогательные функции
├── tests/
│   ├── __init__.py
│   └── test_hh_parser.py
├── .env.example
├── AGENTS.md                 # Правила для AI-агентов и разработки
├── README.md
└── requirements.txt
```
 
---
 
## Требования
 
- Python 3.10+
- Google Chrome или Chromium
- ChromeDriver (версия совпадает с браузером)
---
 
## Установка
 
```bash
git clone https://github.com/your-username/HHParser.git
cd HHParser
 
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
 
pip install -r requirements.txt
```
 
Скопируйте файл с переменными окружения и отредактируйте при необходимости:
```bash
cp .env.example .env
```
 
---
 
## Запуск
 
```bash
python -m app.main
```
 
---
 
## Конфигурация
 
Все параметры задаются через `.env` или переменные окружения:
 
| Переменная       | По умолчанию    | Описание                              |
|------------------|-----------------|---------------------------------------|
| `SEARCH_QUERY`   | `Руководитель отдела маркетинга` | Поисковый запрос          |
| `SALARY`         | `150000`        | Минимальная зарплата (RUB)            |
| `AREA`           | `1`             | Регион поиска на hh.ru                |
| `CURRENCY_CODE`  | `RUR`           | Валюта зарплаты                       |
| `EXPERIENCE`     | `doesNotMatter` | Требуемый опыт                        |
| `ORDER_BY`       | `relevance`     | Сортировка результатов                |
| `SEARCH_PERIOD`  | `0`             | Период публикации вакансий            |
| `ITEMS_ON_PAGE`  | `100`           | Количество вакансий на странице       |
| `MAX_PAGES`      | `5`             | Максимальное число страниц            |
| `OUTPUT_FILE`    | `vacancies.csv` | Имя выходного файла                   |
| `DELAY_MIN`      | `2.0`           | Минимальная пауза между запросами (с) |
| `DELAY_MAX`      | `4.5`           | Максимальная пауза между запросами (с)|
| `PAGE_TIMEOUT`   | `30`            | Таймаут ожидания элементов (с)        |
| `HEADLESS`       | `true`          | Запуск браузера без GUI               |
| `CHROMEDRIVER_PATH` | `/usr/bin/chromedriver` | Путь к ChromeDriver        |
| `BASE_SEARCH_URL` | `https://hh.ru/search/vacancy` | URL поиска hh.ru      |
 
---
 
## Результат
 
Файл `vacancies.csv` (разделитель `;`, кодировка UTF-8 BOM — открывается в Excel без настроек):
 
```
Вакансия;Компания;Ссылка;Описание вакансии;Ключевые навыки
Руководитель отдела маркетинга;ООО Ромашка;https://hh.ru/vacancy/123456;...;SEO, Аналитика
...
```
 
---
 
## Тесты
 
```bash
pytest tests/
```
 
---
 
## requirements.txt
 
```
selenium>=4.20.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pytest>=7.0.0
black>=24.0.0
```
