from pydantic import BaseModel, Field

# --- 1. List 데이터용 Class

class ChartDataItem(BaseModel):
    """차트 데이터의 한 항목을 나타내는 모델 (예: {"label": "00", "value": 150})"""
    label: str
    value: float  

class TopMenuItem(BaseModel):
    """판매 예상 TOP 메뉴의 구조"""
    label: str = Field(description="메뉴 이름")
    value: int = Field(description="메뉴 순위")


# --- 2. API 요청 모델 ---

class AnalysisContext(BaseModel):
    """API가 받을 모든 데이터를 담는 단일 'context' 객체의 상세 명세"""
    
    # 권장 업종
    recommended_industry: str # 권장 업종
    
    # 분석 요청 테이블
    request_polygon_id : str # 요청 폴리곤 아이디
    startup_type_seq: str # 희망 창업 유형 코드
    location_condition: str # 희망 입지 조건 코드
    
    #commercial_type_level: str # GIS 통계 테이블 필드 제거
    # competition_level: str # GIS 통계 테이블 필드 제거

    # 상권 개요

    commercial_type: str # 상권 유형 추가
    timely_population_chart_data: list[ChartDataItem]
    daily_population_chart_data: list[ChartDataItem]
    gender_ratio_chart_data: list[ChartDataItem]
    age_distribution_chart_data: list[ChartDataItem]
    
    # 경쟁 분석
    general_store_cnt: int
    franchise_store_cnt: int
    avg_monthly_sales: int
    top_selling_menus_status_data: list[TopMenuItem] # TOP 메뉴도 label/value 구조
    
    # 입지평가 테이블
    evaluation_content: str # 평가내용
    overall_score: str # 종합점수
    recommended_polygon_id: str # 추천 입지의 polygon_id
    area: str # 해당 polygon_id의 환산 값

class AnalysisInput(BaseModel):
    """API가 최종적으로 받을 요청 본문(Request Body)의 전체 구조"""
    context: AnalysisContext


class FullReportResponse(BaseModel):
    """클라이언트에게 반환될 최종 API 응답(Response)의 전체 구조"""
    price_strategy: list[str] 
    operation_strategy: list[str]  
    title: str
    summary: list[str]
