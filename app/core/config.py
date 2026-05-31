from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "QuanLyKhamBenh"
    API_V1_STR: str = "/api/v1"
    
    # DB (SQL Server)
    SQLSERVER_HOST: str = os.getenv("SQLSERVER_HOST", "localhost\\SQLEXPRESS")
    SQLSERVER_DB: str = os.getenv("SQLSERVER_DB", "QuanLyDatLichKham")
    SQLSERVER_USER: str = os.getenv("SQLSERVER_USER", "sa")
    SQLSERVER_PASSWORD: str = os.getenv("SQLSERVER_PASSWORD", "YourStrongPassword")
    
    SECRET_KEY: str = "2b8a0d9e8c715f4e0c92d5c19e34a6e0c29f4a81bc7e1a6c4d7f8a3e9c2b1a8d"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    @property
    def sqlserver_uri(self) -> str:
        # Using pyodbc with Windows Authentication
        import urllib.parse
        return f"mssql+pyodbc://{self.SQLSERVER_HOST}/{self.SQLSERVER_DB}?driver=SQL+Server&Trusted_Connection=yes"
        
settings = Settings()
