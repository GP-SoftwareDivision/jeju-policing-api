# vertexai.init() 부분을 main.py로 옮겼으므로 여기서는 삭제합니다.
import json
from vertexai.generative_models import GenerativeModel, GenerationConfig
from app.core.config import settings
from app.schema.llm_schema import AnalysisInput  

def _create_briefing_document(context_data) -> str:

        context_items = []

        context_items.append("[분석 주제]")
        context_items.append(f"- 추천 업종: {context_data.recommended_industry}")
        
        context_items.append("\n[상권 특성]")
        context_items.append(f"- 상권 유형: {context_data.commercial_type_level}")
        context_items.append(f"- 경쟁 강도: {context_data.competition_level}")

        gender_str = ", ".join([f"{item.label} {item.value}%" for item in context_data.gender_ratio_chart_data])
        age_str = ", ".join([f"{item.label} {item.value}%" for item in context_data.age_distribution_chart_data])
        daily_str = ", ".join([f"{item.label}({item.value}명)" for item in context_data.daily_population_chart_data])
        timely_str = ", ".join([f"{item.label}시({item.value}명)" for item in context_data.timely_population_chart_data])
        context_items.append("\n[고객 및 유동인구 분석]")
        
        context_items.append(f"- 성별 분포: {gender_str}")
        context_items.append(f"- 연령별 분포: {age_str}")
        context_items.append(f"- 요일별 유동인구: {daily_str}")
        context_items.append(f"- 시간대별 유동인구: {timely_str}")

        context_items.append("\n[경쟁 환경]")
        context_items.append(f"- 일반 점포 수: {context_data.general_store_cnt}개")
        context_items.append(f"- 프랜차이즈 점포 수: {context_data.franchise_store_cnt}개")

        menus_str = ", ".join([f"{item.rank}위({item.menu_name})" for item in context_data.top_selling_menus_status_data])
        context_items.append("\n[수익성 예측]")
        context_items.append(f"- 예상 월 매출: {context_data.avg_monthly_sales // 10000}만원")
        context_items.append(f"- 인기 예상 메뉴: {menus_str}")

        context_items.append(f"\n[입지 평가 의견]: {context_data.evaluation_content}")


        return "\n".join(context_items)


def generate_full_report(request_input: AnalysisInput) -> dict:
        
    context_data = request_input.context
    briefing_document = _create_briefing_document(context_data)

    fixed_system_prompt  = "너는 대한민국 최고의 상권 분석 전문가이자 비즈니스 전략 컨설턴트다."

    summary_instruction = (
        "[모든 분석을 종합한 최종 요약 보고서. 각 문장을 배열(array)의 요소로 구성.]\\n"
        "예시:\\n"
        "[\"종합적으로 본 상권에서는 '[추천 업종]'이 가장 적합합니다.\", "
        "\"권장 입지는 유동인구가 많은 '[권장 입지]'이며, 중저가 메뉴와 테이크아웃 중심 운영을 통해 경쟁력을 확보하는 것이 좋습니다.\", "
        "\"주요 타깃은 20~30대 여성이며, 주말 피크타임에 마케팅 역량을 집중하는 전략을 추천합니다.\"]\\n\\n"
        "**참고: 위 예시는 참고사항일 뿐이며, 제공된 컨텍스트에 맞춰 내용을 창의적으로 분석하되, 각 문장을 배열의 요소로 만드는 형식은 유지해야 합니다.**"
        "**참고: 소상공인에게 권장할 '[권장 입지]'는'[입지 평가 의견]'에 포함되어 있다.**"
    )

    task_instruction = f"""
    [작업 지시]

    **가장 중요한 원칙: 너의 모든 답변은 반드시 '[상권 브리핑 자료]'에 명시된 사실에 근거해야 한다. 브리핑 자료와 모순되거나 근거 없는 추측을 해서는 절대 안 된다.**

    위 원칙에 따라, '[상권 브리핑 자료]'를 상세히 분석하여 '{context_data.recommended_industry}' 업종에 대한 '제목', '가격 전략', '운영 전략', '최종 요약'을 생성해야 한다.
    반드시 아래 '[JSON 결과물 양식]'과 동일한 JSON 형식으로만 답변해야 한다.

    **참고: '[상권 브리핑 자료]'에 포함된 '인기 예상 메뉴' 정보는 해당 업종의 시장 트렌드를 보여주는 참고자료일 뿐, 의뢰인이 확정한 메뉴가 아닙니다. 이 점을 감안하여 메뉴 관련 전략을 제안하세요.**

    [상권 브리핑 자료]
    {briefing_document}

    [JSON 결과물 양식]
    {{
      "title": "[보고서 내용 전체를 대표하는 간결하고 전문적인 제목]",
      "price_strategy": "[핵심 가격 전략을 나타내는 키워드 또는 짧은 구(phrase)의 배열(array). 예: [\"중저가 전략\", \"회전율 중심\", \"가성비 세트 메뉴\"]]",
      "operation_strategy": "[핵심 운영 전략을 나타내는 키워드 또는 짧은 구(phrase)의 배열(array). 예: [\"테이크아웃 집중\", \"주말 피크타임 인력 보강\", \"SNS 감성 마케팅\"]]",
      "summary": {summary_instruction}
    }}
    """

    generation_config = GenerationConfig(temperature=1.0, max_output_tokens=4096)
    model = GenerativeModel(model_name=settings.LLM_MODEL_NAME, system_instruction=fixed_system_prompt)

    try:
        # 3. AI 호출
        response = model.generate_content(task_instruction, generation_config=generation_config)
        print(response)
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
            return {"error": "AI로부터 응답을 받지 못했습니다. (안전 설정에 의해 차단되었을 수 있음)"}

    except Exception as e:
        print(f"Vertex AI 호출 중 오류 발생: {e}")
        return {"error": f"AI 서비스 호출 중 서버 오류 발생: {str(e)}"}


