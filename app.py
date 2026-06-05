import streamlit as st
import google.genai as genai
from pypdf import PdfReader

# 1. 페이지 전체 너비를 넓게 쓰고 깔끔한 타이틀 설정
st.set_page_config(page_title="전시 부스 PM 규정 분석기", layout="wide", page_icon="🎪")

# 2. 가독성을 위한 커스텀 스타일 (글자 크기 및 여백 조정)
st.markdown("""
    <style>
    .report-box {
        background-color: #1E1E24;
        padding: 20px;
        border-radius: 10px;
        line-height: 1.8;
    }
    h3 { margin-top: 20px !important; color: #FF4B4B; }
    li { margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎪 전시 부스 Regulation 자동 분석기")
st.caption("두꺼운 규정집 PDF를 올리면 AI가 핵심 일정과 시공 규정을 가독성 높은 대시보드로 요약해 줍니다.")
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
        with st.spinner("🤖 AI가 규정집을 정독하는 중... 잠시만 기다려주세요."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # 💡 표(Table) 대신 단락과 리스트 형태로 출력하도록 프롬프트 전면 수정
                prompt = f"""
                당신은 베테랑 전시 부스 PM입니다. 제공된 전시 규정집 텍스트를 분석하여 PM이 현장에서 즉시 체크할 수 있는 요약본을 작성해 주세요.
                
                🚨 [출력 규칙 - 절대 준수]:
                1. 절대로 마크다운 표(Table) 양식을 사용하지 마세요. (화면이 찌그러집니다)
                2. 절대로 <br>, <b>, </b> 같은 HTML 태그를 답변에 포함하지 마세요.
                3. 모든 내용은 아래 가이드라인에 맞춰 큰 제목(###)과 글머리 기호(- 또는 *)를 사용한 '리스트 형태'로 작성하세요. 항목이 많다면 가독성을 위해 항목별로 줄바꿈을 많이 하세요.
                
                [출력 양식 가이드라인]:
                ### 1. 기본 정보 & 전시 일정
                - 전시 장소: (장소 이름 및 홀 번호 정확히 입력)
                - 전시 날짜 및 운영 시간: 
                
                ### 2. 부스 설치 및 철거 일정 (D-Day 및 시간 필수)
                - 독립부스 설치(장치공사) 기간: 
                - 독립부스 철거 기간: 
                - 특이사항 (예: 초과 근무 비용, 야간 작업 신청 등): 
                
                ### 3. 주요 행정 신고 마감일 (PM 핵심 체크)
                - 도면 제출 및 기술검토 신고 마감: 
                - 유틸리티(전기/인터넷/급배수 등) 신청 마감: 
                - 기타 부스 활동 및 배지 신청 마감: 
                
                ### 4. 부스 시공 및 디자인 제한 규정
                - 부스 제한 높이 (최대 허용 높이 및 구역별 예외): 
                - 바닥단(Platform) 필수 유무 및 높이 규정: 
                - 디자인 제한 요소 (통로 면 벽면 폐쇄 제한, 방염 규정, 리깅 제한 등): 
                
                ### 5. 기타 중요 특이사항 (페널티 등)
                - (조기 철거 페널티, 반입 금지 물품, 화물 운송 등 중요 내용 요약)
                
                [원본 규정집 텍스트]:
                {raw_text[:35000]}
                """
                
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                
                st.markdown("---")
                st.subheader("📊 AI 규정 분석 결과 대시보드")
                
                # 💡 결과물 출력을 감싸서 가독성을 높임
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
