import streamlit as st
import google.genai as genai
from pypdf import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="전시 부스 PM 규정 분석기", layout="wide", page_icon="🎪")

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
    
    /* 타임라인 표 가독성 높이기 */
    table { width: 100% !important; margin-top: 15px; border-collapse: collapse; }
    th { background-color: #FF4B4B !important; color: white !important; font-weight: bold; text-align: center !important; }
    td { padding: 12px !important; }
    tr:nth-child(even) { background-color: #2D2D35; }
    </style>
""", unsafe_allow_html=True)

st.title("🎪 전시 부스 Regulation 자동 분석기")
st.caption("두꺼운 규정집 PDF를 올리면 AI가 핵심 일정과 시공 규정, 그리고 날짜순 타임라인 표까지 한눈에 요약해 줍니다.")
st.markdown("---")

# 3. API 키 불러오기
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("🔑 API 키가 설정되지 않았습니다. Streamlit 대시보드에서 Secrets 설정을 확인해 주세요.")
    st.stop()

uploaded_file = st.file_uploader("전시 규정집 PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("📄 PDF 텍스트를 추출하는 중입니다..."):
        reader = PdfReader(uploaded_file)
        raw_text = "".join([page.extract_text() + "\n" for page in reader.pages])
    st.success("텍스트 추출 완료!")
    
    if st.button("🪄 규정 분석 시작하기"):
        with st.spinner("🤖 AI가 규정집을 정독하며 타임라인을 생성하는 중입니다... 잠시만 기다려주세요."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # 💡 맨 마지막에 날짜순 정렬 표를 만들도록 프롬프트 정교화
                prompt = f"""
                당신은 베테랑 전시 부스 PM입니다. 제공된 전시 규정집 텍스트를 분석하여 아래 양식에 맞춰 요약본을 작성해 주세요.
                
                🚨 [중요 출력 규칙]:
                1. 절대로 본문 내용 중에는 <br>, <b>, </b> 같은 HTML 태그를 사용하지 마세요.
                2. 1번부터 5번 항목까지는 '글머리 기호 리스트' 형태로 자세하게 작성하세요.
                3. 맨 마지막 '6. PM 핵심 일정 타임라인' 항목은 반드시 규정집에 나온 모든 일정(도면 신고, 전기/유틸리티 신청, 설치 기간, 제품 반입, 전시 기간, 철거 기간 등)을 찾아내어 **[날짜가 빠른 순서대로(오름차순)]** 정렬한 마크다운 표(Table)로 만드세요.
                
                [출력 양식]:
                ### 1. 기본 정보 & 전시 일정
                - 전시 장소: 
                - 전시 날짜 및 운영 시간: 
                
                ### 2. 부스 설치 및 철거 일정
                - 독립부스 설치(장치공사) 기간: 
                - 독립부스 철거 기간: 
                
                ### 3. 주요 행정 신고 마감일
                - 도면 제출 및 기술검토 신고 마감: 
                - 유틸리티(전기/인터넷/급배수 등) 신청 마감: 
                - 기타 마감일: 
                
                ### 4. 부스 시공 및 디자인 제한 규정
                - 부스 제한 높이: 
                - 바닥단(Platform) 규정: 
                - 디자인 제한 요소: 
                
                ### 5. 기타 중요 특이사항
                - (반입 금지, 페널티 등 요약)
                
                ### 6. 🕒 PM 핵심 일정 타임라인 (날짜순 정렬)
                *규정집에 명시된 모든 마감일과 공사 일정을 시간 순서대로 정리한 표입니다.*
                
                | 날짜 (Date) | 시간 (Time) | 해야 할 일 / 주요 일정 (Task) | 비고 및 중요도 (Notice) |
                | :--- | :--- | :--- | :--- |
                | 예: 2026-07-16 | ~ 18:00까지 | 부스 활동 및 프로모션 풍선 신청 마감 | 마감 엄수 |
                | 예: 2026-08-29 | 06:00 ~ 17:00 | 독립부스 장치공사(설치) 시작 | 자재 반입 시간 확인 |
                
                [원본 규정집 텍스트]:
                {raw_text[:35000]}
                """
                
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                
                st.markdown("---")
                st.subheader("📊 AI 규정 분석 결과 대시보드")
                
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
