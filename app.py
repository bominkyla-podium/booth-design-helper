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
    
    /* 중요 디자인 규정 강조 박스 */
    .design-danger-box {
        background-color: #2D1B1B;
        border-left: 5px solid #FF4B4B;
        padding: 15px;
        border-radius: 5px;
        margin-top: 15px;
    }
    
    table { width: 100% !important; margin-top: 15px; border-collapse: collapse; }
    th { background-color: #FF4B4B !important; color: white !important; font-weight: bold; text-align: center !important; }
    td { padding: 12px !important; }
    tr:nth-child(even) { background-color: #2D2D35; }
    </style>
""", unsafe_allow_html=True)

st.title("🎪 전시 부스 시공사용 Regulation 자동 분석기")
st.caption("일정뿐만 아니라 부스 높이 제한, 리깅(Rigging) 규정 등 시공/디자인 제한 사항을 극대화하여 분석합니다.")
st.markdown("---")

# 3. API 키 불러오기
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("🔑 API 키가 설정되지 않았습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

# 4. 사이드바 수동 일정 추가 기능
st.sidebar.header("➕ 나만의 일정 추가하기")
st.sidebar.write("규정집 외에 추가하고 싶은 내부 일정을 입력하세요.")

if "custom_events" not in st.session_state:
    st.session_state.custom_events = pd.DataFrame(
        [{"날짜 (Date)": "2026-08-25", "시간 (Time)": "14:00", "해야 할 일 / 주요 일정 (Task)": "🔥 내부 시공 도면 최종 검수", "비고 및 접수처 (Notice / Where)": "[내부] 회의실"}]
    )

edited_df = st.sidebar.data_editor(
    st.session_state.custom_events, 
    num_rows="dynamic", 
    use_container_width=True
)

st.markdown("### 📄 1. 규정집 파일 업로드 (다중 선택 가능)")
uploaded_files = st.file_uploader("전시 규정집 PDF 파일들을 모두 업로드하세요 (여러 개 선택 가능)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    raw_text = ""
    with st.spinner("📄 업로드된 모든 PDF에서 텍스트를 추출하는 중입니다..."):
        for uploaded_file in uploaded_files:
            reader = PdfReader(uploaded_file)
            file_text = "".join([page.extract_text() + "\n" for page in reader.pages])
            raw_text += f"\n--- [파일명: {uploaded_file.name} 에서 추출된 내용] ---\n" + file_text
            
    st.success(f"총 {len(uploaded_files)}개의 파일 텍스트 추출 완료!")
    
    if st.button("🪄 통합 장치공사 규정 분석 시작하기"):
        with st.spinner("🤖 디자인 규정과 스케줄을 정밀 융합하여 분석하는 중..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                custom_text = ""
                if not edited_df.empty:
                    custom_text = "\n[PM이 추가한 수동 일정 목록]:\n"
                    for _, row in edited_df.iterrows():
                        custom_text += f"| {row['날짜 (Date)']} | {row['시간 (Time)']} | {row['해야 할 일 / 주요 일정 (Task)']} | {row['비고 및 접수처 (Notice / Where)']} |\n"

                # 💡 디자인/리깅/높이 제한 분석을 대폭 보완한 프롬프트
                prompt = f"""
                당신은 베테랑 전시 부스 시공사(장치업체)의 현장 소장이자 설계 PM입니다. 제공된 전시 규정집 텍스트들을 분석하여 설계 오류나 현장 오시공을 방지할 수 있는 '디자인 제한 규정'과 '시공 스케줄' 통합 리포트를 작성해 주세요.
                
                🚨 [장치업체 맞춤형 필수 요약 규칙]:
                1. **[디자인 및 시공 제한] 분석 극대화**: 규정집에서 부스 관련 치수 규정을 이 잡듯 찾아내어 상세히 적으세요.
                   - **부스 최대 허용 높이 제한** (독립부스 최고 높이, 블록별/위치별 차등 적용 여부 포함)
                   - **리깅(Rigging / 천장 매달기) 규정** (리깅 가능 여부, 최대 허용 하중, 리깅 가능 높이 및 배선 제한 등)
                   - **2층 부스(복층 부스) 규정** (허용 여부, 구조 계산서 제출 의무, 면적 제한 등)
                   - **바닥단(Platform) 높이 및 경사로 규정**, 인접 부스 벽면 마감 처리 규정(백월 미싱 처리 등)
                2. '전시 기간(오픈 시간)' 정보는 날짜만 심플하게 요약 기재하세요.
                3. **[철거 및 반출 일정]**은 전시 종료 당일 진입 가능 시간, 반출 마감 시간 위주로 구체적으로 적으세요.
                4. '6. 🕒 장치공사 핵심 타임라인' 표에는 규정집 일정과 [PM이 추가한 수동 일정 목록]을 합쳐 날짜순으로 정렬하되, 긴 접수처 문구는 `[온라인]`, `[이메일]` 등으로 축약하세요. 본문 내 HTML 태그는 금지합니다.
                
                [출력 양식]:
                ### 1. 📐 핵심 디자인 및 부스 시공 제한 규정 (가장 중요)
                - **부스 최대 최고 높이 제한**: 
                - **리깅(천장 배너/조명 매달기) 규정**: (가능 여부, 배선, 하중 제한 등)
                - **복층 부스(2층 부스) 규정**: (구조 검토서 및 높이 제약 등)
                - **바닥(플랫폼) 및 인접 벽면(백월) 마감 규정**: (시각적 차폐, 방염 등)
                
                ### 2. 기본 정보 & 전시 일정 (요약)
                - 전시 장소 및 전시회 정보: 
                - 전시 기간: 
                
                ### 3. 부스 설치(장치공사) 일정
                - 독립부스 설치 기간 및 시간: 
                - 공사 연장 신청 및 야간 작업 관련 규정: 
                
                ### 4. 🔥 철거 및 자재 반출 일정 (디테일 분석)
                - 장치업체 현장 진입 및 철거 개시 가능 시간: 
                - 장치 자재 철거 및 폐기물 반출 마감 시간: 
                
                ### 5. 주요 행정 신고 및 안전 규정
                - 도면 제출 및 기술검토 신고: (마감일 및 접수처)
                - 유틸리티(전기/인터넷/급배수 등) 신청: 
                - 방염 규정 및 페널티/관리비 규정: 
                
                ### 6. 🕒 장치공사 핵심 타임라인 (통합 파일 날짜순 정렬)
                *모든 업로드 파일의 일정과 PM 추가 일정이 시간 순서대로 통합된 마스터 표입니다. (🔥 표시된 마감일 필수 체크)*
                
                | 날짜 (Date) | 시간 (Time) | 해야 할 일 / 주요 일정 (Task) | 비고 및 접수처 (Notice / Where) |
                | :--- | :--- | :--- | :--- |
                
                {custom_text}
                
                [원본 규정집 텍스트들]:
                {raw_text[:40000]}
                """
                
                response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                
                st.markdown("---")
                st.subheader("📊 통합 장치공사 규정 분석 결과 대시보드")
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
