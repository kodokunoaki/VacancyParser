from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    search_query: str = "Руководитель отдела маркетинга"
    salary: int = 150000
    area: int = 1
    currency_code: str = "RUR"
    experience: str = "doesNotMatter"
    order_by: str = "relevance"
    search_period: int = 0
    items_on_page: int = 100
    max_pages: int = 5
    output_file: str = "vacancies.csv"
    delay_min: float = 1.5
    delay_max: float = 3.2
    page_timeout: int = 30
    headless: bool = True
    chromedriver_path: str = "/usr/bin/chromedriver"
    base_search_url: str = "https://hh.ru/search/vacancy"
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
