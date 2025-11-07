# vertexai.init() 부분을 main.py로 옮겼으므로 여기서는 삭제합니다.
import json
import time
from vertexai.generative_models import GenerativeModel, GenerationConfig
from app.core.config import settings
from app.schema.llm_schema import AnalysisInput  

def _create_briefing_document(context_data) -> str:

        context_items = []

        context_items.append("[분석 주제]")
        context_items.append(f"- 추천 업종: {context_data.recommended_industry}")
        
        context_items.append("\n[사용자 창업 희망 정보]")
        context_items.append(f"- 분석 희망 지역 폴리곤: {context_data.request_polygon_id}")
        context_items.append(f"- 희망 창업 유형: {context_data.startup_type_seq}")
        context_items.append(f"- 희망 입지 조건: {context_data.location_condition}")

        # context_items.append("\n[상권 특성]")
        # context_items.append(f"- 상권 유형: {context_data.commercial_type_level}")
        # context_items.append(f"- 경쟁 강도: {context_data.competition_level}")

        gender_str = ", ".join([f"{item.label} {item.value}%" for item in context_data.gender_ratio_chart_data])
        age_str = ", ".join([f"{item.label} {item.value}%" for item in context_data.age_distribution_chart_data])
        daily_str = ", ".join([f"{item.label}({item.value}명)" for item in context_data.daily_population_chart_data])
        timely_str = ", ".join([f"{item.label}시({item.value}명)" for item in context_data.timely_population_chart_data])
        context_items.append("\n[고객 및 유동인구 분석]")
        
        context_items.append(f"- 상권 유형: {context_data.commercial_type}")
        context_items.append(f"- 성별 분포: {gender_str}")
        context_items.append(f"- 연령별 분포: {age_str}")
        context_items.append(f"- 요일별 유동인구: {daily_str}")
        context_items.append(f"- 시간대별 유동인구: {timely_str}")

        context_items.append("\n[경쟁 환경]")
        context_items.append(f"- 일반 점포 수: {context_data.general_store_cnt}개")
        context_items.append(f"- 프랜차이즈 점포 수: {context_data.franchise_store_cnt}개")

        menus_str = ", ".join([f"{item.value}위({item.label})" for item in context_data.top_selling_menus_status_data])
        context_items.append("\n[수익성 예측]")
        context_items.append(f"- 예상 월 매출: {context_data.avg_monthly_sales // 10000}만원")
        context_items.append(f"- 인기 예상 메뉴: {menus_str}")

        context_items.append("\n[입지 평가 및 추천]")
        context_items.append(f"- 입지 추천 폴리곤: {context_data.recommended_polygon_id}")
        context_items.append(f"- 입지 추천 지역명: {context_data.area}")
        context_items.append(f"- 종합 평가: {context_data.evaluation_content}")
        context_items.append(f"- 종합 점수: {context_data.overall_score}")

        return "\n".join(context_items)


def generate_full_report(request_input: AnalysisInput) -> dict:
        
    context_data = request_input.context
    briefing_document = _create_briefing_document(context_data)

    fixed_system_prompt  = "너는 대한민국 최고의 제주도 상권 분석 전문가이자 비즈니스 전략 컨설턴트다."

    # summary_instruction = (
    #     "[모든 분석을 종합한 최종 요약 보고서. 각 문장을 배열(array)의 요소로 구성.]\\n"
    #     "예시:\\n"
    #     "[\"종합적으로 본 상권에서는 '[추천 업종]'이 가장 적합합니다.\", "
    #     "\"권장 입지는 유동인구가 많은 '[권장 입지]'이며, 중저가 메뉴와 테이크아웃 중심 운영을 통해 경쟁력을 확보하는 것이 좋습니다.\", "
    #     "\"주요 타깃은 20~30대 여성이며, 주말 피크타임에 마케팅 역량을 집중하는 전략을 추천합니다.\"]\\n\\n"
    #     "**참고: 위 예시는 참고사항일 뿐이며, 제공된 컨텍스트에 맞춰 내용을 창의적으로 분석하되, 각 문장을 배열의 요소로 만드는 형식은 유지해야 합니다.**"
    #     "**참고: 소상공인에게 권장할 '[권장 입지]'는'[입지 평가 의견]'에 포함되어 있다.**"
    # )

    task_instruction = f"""
    [작업 지시]

    [입력 데이터]를 바탕으로, [출력 형식]에 맞춰 '분석 보고서'를 JSON 형식으로 생성해야 한다.

    **가장 중요한 원칙: 모든 답변은 반드시 [입력 데이터]에 명시된 사실에 근거해야 한다. [입력 데이터]와 모순되거나 근거 없는 추측을 해서는 절대 안 된다.**
    
    **[Title] 생성 핵심 지침:**
    'title' 필드는 반드시 [희망 창업 유형]을 포함해야 한다.
    (예: [희망 창업 유형] 상권 분석 요약')
    **'[추천 업종]'이 아닌 사용자가 요청한 [희망 창업 유형]을 사용해야 함을 명심하라.**

    **[Summary] 생성 핵심 지침:**
    'summary'는 3개 이상, 5개 이하의 문장으로 구성된 배열(array)이어야 하며, 아래 지침을 따른다.
    **중요: 각 문장은 배열의 독립된 요소(string)여야 합니다. 하나의 문자열 요소에 여러 문장을 절대 넣지 마세요.**
    **따옴표('')를 사용하여 데이터를 단순 삽입하지 말고, 컨설턴트처럼 자연스러운 문장으로 풀어써야 한다.**

    요약 문장은 아래의 내용들을 포함해야 한다.

    1.  **요약 문장 1 (상권 및 업종)**: "이곳은 [상권 유형] 상권의 특성이 강해, 종합적으로 [추천 업종] 운영에 가장 적합한 환경입니다."와 같이 자연스러운 서두로 시작한다.
    
    2.  **요약 문장 2 (입지 선정 및 근거)**: "권장 입지는 [입지 추천 지역명]입니다."

    3.  **요약 문장 3 (입지 선정 근거)**:
    - 먼저 [사용자 창업 희망 정보]의 [분석 희망 지역 폴리곤] ID와 [입지 평가 및 추천]의 [입지 추천 폴리곤] ID를 비교한다.
        - **(ID 동일 시)**: "이곳은 **[종합 평가]의 핵심 내용(예: '안정적 배후수요', '낮은 경쟁 강도')을 자연스럽게 요약**하여 서술한다.
        - **(ID 다름 시)**: "이 지역은 **'[종합 평가]'의 핵심 내용(예: '풍부한 잠재수요', '공급 부족')을 자연스럽게 요약으로, [희망 입지 조건]에 더 부합하기 때문입니다." 형식으로 작성한다. 
    4.  **요약 문장 4 (가격전략)**: [가격 전략 키워드] 중심 운영을 통해 경쟁력을 확보하는 것이 좋습니다.

    5.  **요약 문장 5(타겟 및 세부 전략)**: "주요 고객층은 [연령/성별 핵심 타겟]으로 분석되며, 유동인구가 몰리는 [핵심 시간/요일] 피크타임에 마케팅 역량을 집중하는 전략을 추천합니다." 형식으로 자연스럽게 작성한다.
    
    **중요: JSON 출력 결과에는 '2-1' 같은 폴리곤 ID가 절대 노출되어서는 안 되며, 오직 [입지 추천 지역명]({context_data.area} 값)만 사용해야 한다.**
    반드시 아래 [출력 형식]과 동일한 JSON 형식으로만 답변해야 한다.

    **[전략 키워드 생성 지침]:**
    'price_strategy'와 'operation_strategy'는 [입력 데이터]를 바탕으로 가장 중요하고 핵심적인 키워드를 **정확히 2개씩** 추출하여 배열로 만들어야 한다. **절대로 1개나 3개 이상을 반환해서는 안 된다.**

    [출력 형식]
    {{
      "title": (string) "분석 보고서의 핵심 제목 (반드시 [희망 창업 유형] 포함)",
      "summary": (array[string]) [
        "첫 번째 요약 문장입니다.",
        "두 번째 요약 문장입니다.",
        "세 번째 요약 문장입니다.",
        "네 번째 요약 문장입니다.",
        "다섯 번째 요약 문장입니다.",
      ],
      "price_strategy": (array[string]) [
        "가장 중요한 가격 전략 키워드 1",
        "두 번째로 중요한 가격 전략 키워드 2"
      ],
      "operation_strategy": (array[string]) [
        "가장 중요한 운영 전략 키워드 1",
        "두 번째로 중요한 운영 전략 키워드 2"
      ]
    }}
    
    [입력 데이터]
    {briefing_document}
    """

    generation_config = GenerationConfig(temperature=settings.LLM_TEMPERATURE, max_output_tokens=settings.LLM_MAX_TOKENS)
    model = GenerativeModel(model_name=settings.LLM_MODEL_NAME, system_instruction=fixed_system_prompt)

    try:
        # 3. AI 호출
        start_time = time.time()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> AI 호출 시작...")
        response = model.generate_content(task_instruction, generation_config=generation_config)
        print(response)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] >>> AI 응답 수신 완료! (소요 시간: {elapsed_time:.2f}초)")
        # 4. AI 응답 파싱
        if response.candidates and response.candidates[0].content.parts:
            response_text = response.candidates[0].content.parts[0].text
            clean_json_str = response_text.strip().replace("```json", "").replace("```", "")
            try:
                return json.loads(clean_json_str)
            except json.JSONDecodeError:
                print(f"AI 응답 JSON 파싱 오류: {clean_json_str}")
                return {"error": "AI가 유효한 JSON을 생성하지 못했습니다."}
        else:
            return {"error": "AI로부터 응답을 받지 못했습니다."}

    except Exception as e:
        print(f"Vertex AI 호출 중 오류 발생: {e}")
        return {"error": f"AI 서비스 호출 중 서버 오류 발생: {str(e)}"}


