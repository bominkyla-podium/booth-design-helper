import streamlit as st
import google.genai as genai
from pypdf import PdfReader
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="전시 부스 시공사용 규정 분석기", layout="wide", page_icon="🎪")

# 2. 커스텀 스타일
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
    
    table { width: 100% !important; margin-top: 15px; border-collapse: collapse; }
    th { background-color: #FF4B4B !important; color: white !important; font-weight: bold; text-align: center !important; }
    td { padding: 12px !important; }
    tr:nth-child(even) { background-color: #2D2D35; }
    </style>
""", unsafe_allow_html=True)

st.title("🎪 전시 부스 시공사용 Regulation 자동 분석기")
st.caption("규정집 PDF 요약은 물론, 내가 직접 입력한 개별 일정까지 합쳐서 하나의 타임라인으로 정렬해 줍니다.")
st.markdown("---")

# 3. API 키 불러오기
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("🔑 API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

# 💡 [새로운 기능] 개별 일정 추가 섹션 (사이드바에 배치)
st.sidebar.header("➕ 나만의 일정 추가하기")
st.sidebar.write("규정집 외에 추가하고 싶은 내부 일정을 입력하세요. (아래 표에 행을 추가할 수 있습니다)")

# 입력할 기본 틀(데이터프레임) 생성
if "custom_events" not in st.session_state:
    st.session_state.custom_events = pd.DataFrame(
        [{"날짜 (Date)": "2026-08-25", "시간 (Time)": "14:00", "해야 할 일 / 주요 일정 (Task)": "🔥 내부 시공 도면 최종 검수", "비고 및 접수처 (Notice / Where)": "[내부] 회의실"}],
    )

# 엑셀처럼 직접 입력할 수 있는 표 띄우기
edited_df = st.sidebar.data_editor(
    st.session_state.custom_events, 
    num_rows="dynamic",  # 사용자가 행을 마음대로 추가/삭제 가능
    use_container_width=True
)

st.markdown("### 📄 1. 규정집 파일 업로드")
uploaded_file = st.file_uploader("전시 규정집 PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("📄 PDF 텍스트를 추출하는 중입니다..."):
        reader = PdfReader(uploaded_file)
        raw_text = "".join([page.extract_text() + "\n" for page in reader.pages])
    st.success("텍스트 추출 완료!")
    
    if st.button("🪄 장치공사 규정 분석 시작하기"):
        with st.spinner("🤖 내 일정과 규정집을 합쳐서 타임라인을 병합하는 중..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # 사용자가 사이드바에 입력한 커스텀 일정을 텍스트 형식으로 변환
                custom_text = ""
                if not edited_df.empty:
                    custom_text = "\n[PM이 추가한 수동 일정들]:\n"
                    for _, row in edited_df.iterrows():
                        custom_text += f"| {row['날짜 (Date)']} | {row['시간 (Time)']} | {row['해야 할 일 / 주요 일정 (Task)']} | {row['비고 및 접수처 (Notice / Where)']} |\n"

                prompt = f"""
                당신은 베테랑 전시 부스 시공사(장치업체)의 PM입니다. 제공된 전시 규정집 텍스트와 [PM이 추가한 수동 일정들]을 완벽히 합쳐서 양식에 맞춰 작성해 주세요.
                
                🚨 [장치업체 맞춤형 요약 규칙]:
                1. '전시 기간(오픈 시간)' 정보는 날짜만 심플하게 기재하세요.
                2. **[철거 및 반출 일정]**을 구체적인 시간 위주로 디테일하게 분석하세요.
                3. 본문 내용 중에는 HTML 태그를 사용하지 마세요.
                4. 🚨 **[가장 중요 - 타임라인 병합 규칙]**: 
                   - 아래 원본 텍스트에 있는 일정들과 대괄호 안에 제공된 [PM이 추가한 수동 일정들]을 **하나의 표로 합치세요.**
                   - 합친 후 모든 행을 **[날짜와 시간 순서대로 완벽하게 정렬]**하여 '6. 🕒 장치공사 핵심 타임라인' 표를 완성하세요.
                   - 사용자가 입력한 일정에 '🔥'가 있거나 주요 마감일인 경우 글씨를 볼드체로 강조하세요.
                   - 접수처는 `[온라인]`, `[이메일: 주소]` 형태로 짧게 압축하세요.
                
                [출력 양식]:
                ### 1. 기본 정보 & 전시 일정 (요약)
                - 전시 장소: 
                - 전시 기간: 
                
                ### 2. 부스 설치(장치공사) 일정
                - 독립부스 설치 기간 및 시간: 
                - 공사 연장 신청 및 야간 작업 관련 규정: 
                
                ### 3. 🔥 철거 및 자재 반출 일정 (디테일 분석)
                - 장치업체 현장 진입 및 철거 개시 가능 시간: 
                - 디스플레이품/전시 제품 반출 시간: 
                - 장치 자재 철거 및 폐기물 반출 마감 시간: 
                
                ### 4. 주요 행정 신고 및 접수처
                - 도면
