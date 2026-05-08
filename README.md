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
│   ├── main.py               # CLI-точка входа
│   ├── gui.py                # Tkinter GUI
│   ├── gui_config.py         # Подготовка настроек из формы GUI
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
- Tkinter. На Windows обычно входит в Python. На Linux может понадобиться
  системный пакет `python3-tk`.
- Google Chrome или Chromium
- ChromeDriver не нужно указывать вручную, если Selenium Manager может подобрать
  его автоматически. При необходимости путь можно задать через `CHROMEDRIVER_PATH`.
---
 
## Установка
 
```bash
git clone https://github.com/kodokunoaki/HHParser.git
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
 
## Запуск GUI

```bash
python -m app.gui
```

В окне приложения доступны поля:

- поисковый запрос;
- зарплата от, в рублях;
- максимальное количество страниц;
- имя файла результата без `.csv`;
- количество вакансий на странице: 20, 50 или 100;
- кнопка запуска поиска;
- текущий статус и лог выполнения.

---

## Запуск CLI

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
| `DELAY_MIN`      | `1.5`           | Минимальная пауза между запросами (с) |
| `DELAY_MAX`      | `3.2`           | Максимальная пауза между запросами (с)|
| `PAGE_TIMEOUT`   | `30`            | Таймаут ожидания элементов (с)        |
| `SEARCH_CARDS_WAIT_TIMEOUT` | `5.0` | Короткое ожидание полной выдачи карточек после быстрой загрузки страницы |
| `HEADLESS`       | `true`          | Запуск браузера без GUI               |
| `CHROMEDRIVER_PATH` | пусто | Путь к ChromeDriver. Если пусто, Selenium подбирает драйвер автоматически |
| `PAGE_LOAD_STRATEGY` | `eager` | Стратегия загрузки страниц Chrome: `normal`, `eager` или `none` |
| `DISABLE_IMAGES` | `true`          | Отключать загрузку изображений в Chrome |
| `BASE_SEARCH_URL` | `https://hh.ru/search/vacancy` | URL поиска hh.ru      |

---

## Сборка EXE

Собирать exe нужно из активированного виртуального окружения, где установлены
все зависимости проекта:

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m PyInstaller --clean HHParser.spec
```

Готовый файл появится в `dist/HHParser.exe`.

Если exe падает с ошибкой вида `ModuleNotFoundError: No module named 'pydantic'`,
значит сборка была запущена не из того окружения или зависимости не были
установлены перед сборкой. Удалите папки `build/` и `dist/`, активируйте `venv`,
выполните команды выше и пересоберите exe.

Если после обновления Selenium появляется ошибка вида
`ModuleNotFoundError: No module named 'selenium.webdriver.chrome.webdriver'`,
пересоберите exe по командам выше и замените старый файл в `dist/`.
`HHParser.spec` явно включает Chrome-модули Selenium, которые импортируются
динамически.
 
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
pyinstaller>=6.0.0
```
