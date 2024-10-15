from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str = "127.0.0.1"  # WAMP MySQL server (localhost)
    DB_PORT: str = "3306"  # Default MySQL port on WAMP
    DB_USER: str = "root"  # Default WAMP MySQL user (or your MySQL user)
    DB_PASSWORD: str = ""  # MySQL password, set it if applicable
    DB_NAME: str = "attendance_Data_db"  # The database name you are using

    class Config:
        env_file = ".env"

settings = Settings()
