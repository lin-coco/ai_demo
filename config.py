import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # celery配置
    CELERY_BROKER_URL=os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND=os.getenv("CELERY_RESULT_BACKEND")
    # langchain-openai配置
    OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL")
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL=os.getenv("OPENAI_MODEL")

