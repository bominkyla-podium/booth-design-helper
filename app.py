import streamlit as st
import google.genai as genai
from pypdf import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="전시 부스 시공사용 규정 분석기", layout="wide", page_icon="🎪")

# 2. 가독성을 위한 커스텀 스타일
st.markdown("""
    <style>
    .report-box {
        background-color: #1E1E24;
        padding: 20px;
        border-radius: 10px;
        line-height: 1.8;
    }
    h3 { margin-top: 30px !important; color: #FF4B4B; border-bottom: 2px solid #FF4B4B; padding-bottom: 8px; }
    li { margin-bottom: 8px; }
    
    /* 타임라인 표 가독성 극대화 */
    table { width: 100% !important; margin-top: 15px; border-collapse: collapse; }
    th { background-color: #FF4B4B !important; color: white !important; font-weight: bold; text-align: center !important; }
    td { padding: 12px !important; }
    tr:nth-child(even) { background-color: #2D2D35; }
    </style>
""", unsafe_allow_html=True)

st.title("🎪 전시 부스 시공사용 Regulation 자동 분석기")
st.caption("장치업체 시각에 맞춰 전시 기간은 요약하고, 설치 및 철거(반출) 스케줄을 극대화하여 보여줍니다.")
st.markdown("---")

# 3. API 키 불러오기
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("🔑 API 키가 설정되지 않았습니다. Streamlit 대시보드에서 Secrets 설정 확인 필요.")
    st.stop()

uploaded_file = st.file_uploader("전시 규정집 PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("📄 PDF 텍스트를 추출하는 중입니다..."):
        reader = PdfReader(uploaded_file)
        raw_text = "".join([page.extract_text() + "\n" for page in reader.pages])
    st.success("텍스트 추출 완료!")
    
    if st.button("🪄 장치공사 규정 분석 시작하기"):
        with st.spinner("🤖 시공/철거 스케줄 중심으로 규정집을 정밀 분석하는 중..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # 💡 전시 기간 축소 및 철거 일정 디테일 강화를 위한 프롬프트 수정
                prompt = f"""
                당신은 베테랑 전시 부스 시공사(장치업체)의 PM입니다. 제공된 전시 규정집 텍스트를 분석하여 현장 작업팀과 관리자가 즉시 체크할 수 있는 시공 맞춤형 요약본을 작성해 주세요.
                
                🚨 [장치업체 맞춤형 요약 규칙]:
                1. '전시 기간(오픈 시간)' 정보는 장치업체에게 중요하지 않으므로, 상세 운영시간(매일 몇 시 오픈 등)은 생략하고 날짜만 한 줄로 간단히 퉁쳐서 적으세요.
                2. 대신 **[철거 및 반출 일정]**을 극도로 디테일하게 분석하세요. 전시가 끝나는 당일 몇 시부터 장치업체 출입 및 철거가 가능한지, 자재 및 중장비 반입/반출 시간, 최종 전시장 비워줘야 하는 마감 시간 등을 규정집에서 모두 찾아내어 쪼개서 적으세요.
                3. 본문 내용 중에는 <br>, <b> 등 HTML 태그를 사용하지 말고 글머리 기호 리스트로 작성하세요.
                4. '6. PM 핵심 일정 타임라인' 표는 모든 일정을 **[날짜/시간이 빠른 순서대로]** 정렬하고, 접수처는 `[온라인]`, `[이메일: 주소]` 형태로 짧게 압축하세요. 주요 행정 마감일은 해야 할 일 칸에 '🔥' 아이콘과 볼드체(**글씨**)를 적용하세요.
                
                [출력 양식]:
                ### 1. 기본 정보 & 전시 일정 (요약)
                - 전시 장소: 
                - 전시 기간: (날짜만 심플하게 한 줄로 기재)
                
                ### 2. 부스 설치(장치공사) 일정
                - 독립부스 설치 기간 및 시간: 
                - 공사 연장 신청 및 야간 작업 관련 규정: 
                
                ### 3. 🔥 철거 및 자재 반출 일정 (디테일 분석)
                - 장치업체 현장 진입 및 철거 개시 가능 시간: (전시 마지막 날 구체적인 시간 필수)
                - 디스플레이품/전시 제품 반출 시간: 
                - 장치 자재 철거 및 폐기물 반출 마감 시간: (최종 전시장 인도 마감 시간 포함)
                
                ### 4. 주요 행정 신고 및 접수처
                - 도면 제출 및 기술검토 신고: (마감일 및 접수처)
                - 시공 관리비 및 장치공사 신고 서류: 
                - 유틸리티(전기/인터넷/급배수 등) 신청: 
                
                ### 5. 부스 시공 및 안전/디ain 제한 규정
                - 부스 제한 높이 및 바닥단 규정: 
                - 방염 규정 및 위험물 반입 제한: 
                - 페널티 및 관리비 규정: 
                
                ### 6. 🕒 장치공사 핵심 타임라인 (날짜순 정렬 및 접수처 포함)
                *서류 마감부터 설치, 그리고 철거 디테일까지 시간 순서대로 정리한 표입니다. (🔥 표시된 마감일 필수 체크)*
                
                | 날짜 (Date) | 시간 (Time) | 해야 할 일 / 주요 일정 (Task) | 비고 및 접수처 (Notice / Where) |
                | :--- | :--- | :--- | :--- |
                
                [원본 규정집 텍스트]:
                {raw_text[:35000]}
                """
                
                response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                
                st.markdown("---")
                st.subheader("📊 장치공사 규정 분석 결과 대시보드")
                
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
