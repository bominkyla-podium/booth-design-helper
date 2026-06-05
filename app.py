# 깃허브 app.py에 넣을 웹 배포용 코드
import streamlit as st
import google.genai as genai
from pypdf import PdfReader

st.set_page_config(page_title="전시 부스 PM 규정 분석기", layout="wide", page_icon="🎪")

st.title("🎪 전시 부스 Regulation 자동 분석기")
st.caption("두꺼운 규정집 PDF를 올리면 AI가 핵심 일정과 시공 규정을 대시보드로 요약해 줍니다.")
st.markdown("---")

# 시스템 보안 금고에서 API 키를 안전하게 불러오는 방식입니다.
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
                prompt = f"""
                당신은 베테랑 전시 부스 PM입니다. 제공된 전시 규정집 텍스트를 분석하여 아래 항목들을 빠짐없이 포함하여 '마크다운 표'와 '체크리스트'로 깔끔하게 정리해 주세요.
                
                1. 기본 정보: 전시 장소, 전시 날짜
                2. 주요 일정: 독립부스 설치(장치공사) 및 철거 날짜/시간
                3. 행정 신고 마감일: 도면 및 기술검토 신고 마감일, 전기/인터넷/급배수 신청 마감일
                4. 부스 시공 규정: 부스 제한 높이, 바닥단 필수 유무 및 규정
                5. 디자인 제한 요소: 통로 면 접한 벽면 제한, 방염 규정 등 특이사항
                
                [원본]:
                {raw_text[:30000]}
                """
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.markdown("---")
                st.subheader("📊 AI 규정 분석 결과 대시보드")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
