from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.router import llm_router
from app.core.config import settings
import vertexai

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 실행될 코드
    print("AI 모델을 위한 Vertex AI 초기화를 시작합니다.")
    vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_REGION)
    print("Vertex AI 초기화 완료.")
    
    yield # yield를 기준으로 윗부분이 시작 시, 아랫부분이 종료 시 실행됨

    # 앱 종료 시 실행될 코드 (필요하다면)
    print("애플리케이션을 종료합니다.")

app = FastAPI(
    title="settings.APP_NAME",
    description="An API to get business analysis summary reports from Google's Generative AI models.",
    version="1.0.0",
    lifespan=lifespan # on_event 대신 lifespan 사용
)

app.include_router(llm_router.router)

@app.get("/")
def read_root():
    return {"message": f"Welcome to the {settings.APP_NAME} API"}