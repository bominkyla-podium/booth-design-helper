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

# 4. 사이드바 수동 일정 추가 기능
st.sidebar.header("➕ 나만의 일정 추가하기")
st.sidebar.write("규정집 외에 추가하고 싶은 내부 일정을 입력하세요. (엑셀처럼 칸을 더블클릭해 수정하고 행을 추가할 수 있습니다)")

# 기본 샘플 틀 데이터 제공
if "custom_events" not in st.session_state:
    st.session_state.custom_events = pd.DataFrame(
        [{"날짜 (Date)": "2026-08-25", "시간 (Time)": "14:00", "해야 할 일 / 주요 일정 (Task)": "🔥 내부 시공 도면 최종 검수", "비고 및 접수처 (Notice / Where)": "[내부] 회의실"}]
    )

# 데이터 에디터 실행
edited_df = st.sidebar.data_editor(
    st.session_state.custom_events, 
    num_rows="dynamic", 
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
                
                # 수동 일정 문자열 변환 처리
                custom_text = ""
                if not edited_df.empty:
                    custom_text = "\n[PM이 추가한 수동 일정 목록]:\n"
                    for _, row in edited_df.iterrows():
                        custom_text += f"| {row['날짜 (Date)']} | {row['시간 (Time)']} | {row['해야 할 일 / 주요 일정 (Task)']} | {row['비고 및 접수처 (Notice / Where)']} |\n"

                # 에러 유발 가능성이 있는 중괄호 구조를 안전하게 맵핑한 프롬프트
                prompt = f"""
                당신은 베테랑 전시 부스 시공사(장치업체)의 PM입니다. 제공된 전시 규정집 텍스트와 하단의 [PM이 추가한 수동 일정 목록]을 완벽히 병합하여 시공용 요약본을 작성해 주세요.
                
                🚨 [장치업체 맞춤형 요약 규칙]:
                1. '전시 기간(오픈 시간)' 정보는 상세 운영시간을 제외하고 날짜만 심플하게 기재하세요.
                2. **[철거 및 반출 일정]**을 구체적인 시간 위주로 디테일하게 분석하세요. 전시 종료 당일 진입 가능 시간, 반출 마감 시간 등이 필수 포함되어야 합니다.
                3. 본문 내용 중에는 HTML 태그를 사용하지 마세요.
                4. 🚨 **[타임라인 표 병합 및 정렬 규칙]**: 
                   - 원본 규정집에서 찾아낸 일정들과 제공된 [PM이 추가한 수동 일정 목록]을 **하나의 마크다운 표로 합치세요.**
                   - 합친 후 모든 행을 **[날짜와 시간 순서대로 완벽하게 정렬]**하여 '6. 🕒 장치공사 핵심 타임라인' 표를 만드세요.
                   - 접수처는 'Online Exhibitor Service Center' 같은 긴 문구 대신 `[온라인]`, `[온라인 포털]` 혹은 `[이메일: 주소]` 형태로 무조건 짧게 축약하세요. 정보가 없다면 간단히 `[-]`로 채우세요.
                   - 주요 행정 마감일이나 필수 체크 일정은 해야 할 일 칸에 '🔥' 아이콘과 볼드체(**글씨**)를 적용하세요.
                
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
                - 도면 제출 및 기술검토 신고: 
                - 시공 관리비 및 장치공사 신고 서류: 
                - 유틸리티(전기/인터넷/급배수 등) 신청: 
                
                ### 5. 부스 시공 및 안전/디자인 제한 규정
                - 부스 제한 높이 및 바닥단 규정: 
                - 방염 규정 및 위험물 반입 제한: 
                - 페널티 및 관리비 규정: 
                
                ### 6. 🕒 장치공사 핵심 타임라인 (수동 일정 포함 날짜순 정렬)
                *규정집 일정과 PM 추가 일정이 시간 순서대로 통합된 표입니다. (🔥 표시된 마감일 필수 체크)*
                
                | 날짜 (Date) | 시간 (Time) | 해야 할 일 / 주요 일정 (Task) | 비고 및 접수처 (Notice / Where) |
                | :--- | :--- | :--- | :--- |
                
                {custom_text}
                
                [원본 규정집 텍스트]:
                {raw_text[:35000]}
                """
                
                response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                
                st.markdown("---")
                st.subheader("📊 장치공사 규정 분석 결과 대시보드")
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
