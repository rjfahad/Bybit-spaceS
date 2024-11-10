from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str


    REF_LINK: str = ""


    AUTO_TASK: bool = True
    AUTO_GAME: bool = True


    DELAY_EACH_ACCOUNT: list[int] = [20, 30]
    SLEEP_TIME_EACH_ROUND: list[int] = [2, 3]

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()

