from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    KEYCLOAK_SERVER_URL : str
    KEYCLOAK_REALM : str
    KEYCLOAK_CLIENT_ID : str
    KEYCLOAK_CLIENT_SECRET : str
    KEYCLOAK_ADMIN_USER : str
    KEYCLOAK_ADMIN_PASSWORD : str
    
    # S3 endpoints
    AWS_S3_ENDPOINT : str
    AWS_ACCESS_KEY_ID : str
    AWS_SECRET_ACCESS_KEY : str
    S3_BUCKET_NAME : str
    S3_REGION : str
    AWS_VIRTUAL_HOSTING: str
    AWS_HTTPS:str
    CPL_VSIL_CURL_USE_S3:str
    AWS_NO_SIGN_REQUEST:str
    AWS_S3_PROTOCOL:str
    
    # Airflow config
    AIRFLOW_USER_USERNAME:str
    AIRFLOW_USER_PASSWORD:str
    AIRFLOW_API_BASE_URL:str
    
    class Config:
        env_file = ".env"
        case_sensitive = True # Ensure environment variables are case-sensitive
        extra = "ignore" # Ignore extra env vars not defined in model

settings = Settings(_env_file=".env") # Pass env file explicitly
