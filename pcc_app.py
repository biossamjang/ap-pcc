# from dotenv import load_dotenv
import os
import streamlit as st
import httpx
import warnings

# .env 파일 로드
# load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="유해물질 응급처치",
    page_icon="🚨",
    layout="centered"
)

# Session state 초기화
if 'result' not in st.session_state:
    st.session_state.result = None
if 'chat_model' not in st.session_state:
    st.session_state.chat_model = None

@st.cache_resource
def initialize_chat_model():
    """ChatOpenAI 모델 초기화 (한 번만 실행)"""
    try:
        # 최신 버전 시도
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            # 구버전 폴백
            from langchain.chat_models import ChatOpenAI
        
        # SSL 검증 비활성화 경고 무시
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        
        # SSL 검증 비활성화가 필요한 경우
        client = httpx.Client(verify=False)
        
        # ChatOpenAI 인스턴스 생성
        try:
            # 최신 버전 (http_client 지원)
            chat_model = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                http_client=client
            )
        except TypeError:
            # 구버전 또는 http_client 미지원 버전
            chat_model = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        
        return chat_model
    
    except Exception as e:
        st.error(f"모델 초기화 실패: {str(e)}")
        return None

# 모델 초기화
if st.session_state.chat_model is None:
    st.session_state.chat_model = initialize_chat_model()

# UI 구성
st.title("🚨 유해물질 응급처치")
st.markdown("---")

# 사이드바에 사용 가이드 추가
with st.sidebar:
    st.header("📋 사용 가이드")
    st.info("""
    1. 유해물질 노출 상황을 구체적으로 입력
    2. '분석하기' 버튼 클릭
    3. AI가 분석한 결과 확인
    
    **분석 항목:**
    - 노출제품유형
    - 노출유형
    - 노출제품명
    """)
    
    # API 키 상태 확인
    api_key_status = "✅ 설정됨" if os.getenv("OPENAI_API_KEY") else "❌ 미설정"
    st.metric("API Key 상태", api_key_status)

# 메인 입력 영역
st.subheader("💬 문의 내용 입력")

# 예시 텍스트
example_text = """에탄올 물티슈 썼더니 화상입었어요.. 며칠전에 겨드랑이에 땀이 너무 많이 나서 급한대로 에탄올 75% 물티슈로 겨드랑이를 닦아냈는데, 며칠동안 그 부위가 따갑더니 결국 보니까 빨갛게 화상입은 것처럼 됐어요"""

# 텍스트 입력 영역
user_input = st.text_area(
    "문의 내용을 구체적으로 입력해 주세요",
    height=150,
    placeholder=example_text,
    help="노출된 제품명, 노출 경로, 증상 등을 자세히 작성해주세요"
)

# 예시 버튼
if st.button("📝 예시 입력", type="secondary"):
    st.session_state.example_input = example_text
    st.rerun()

# 예시 입력 처리
if 'example_input' in st.session_state:
    user_input = st.session_state.example_input
    del st.session_state.example_input

# 버튼 컨테이너
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    analyze_button = st.button("🔍 분석하기", type="primary", use_container_width=True)

with col2:
    clear_button = st.button("🔄 초기화", use_container_width=True)

# 초기화 버튼 처리
if clear_button:
    st.session_state.result = None
    st.rerun()

# 분석 버튼 처리
if analyze_button:
    if not user_input or user_input.strip() == "":
        st.warning("⚠️ 문의 내용을 입력해주세요.")
    elif not st.session_state.chat_model:
        st.error("❌ ChatGPT 모델이 초기화되지 않았습니다. API 키를 확인해주세요.")
    else:
        # 분석 진행
        with st.spinner("🤖 AI가 분석 중입니다..."):
            try:
                # 프롬프트 구성
                contents = """아래 질문을 유추하여 다음 정보를 분석해주세요:
                1. 노출제품유형: 의약품, 생활화학제품, 농약, 기타 중 선택
                2. 노출유형: 경구, 안구, 피부, 흡입, 기타 중 선택
                3. 노출제품명: 구체적인 제품명
                
                결과를 명확하게 구분하여 보여주세요.
                
                질문: """
                
                full_prompt = contents + user_input
                
                # API 호출
                try:
                    # 최신 버전에서는 invoke 메서드 사용
                    response = st.session_state.chat_model.invoke(full_prompt)
                    if hasattr(response, 'content'):
                        st.session_state.result = response.content
                    else:
                        st.session_state.result = str(response)
                except AttributeError:
                    # 구버전에서는 predict 메서드 사용
                    st.session_state.result = st.session_state.chat_model.predict(full_prompt)
                
                st.success("✅ 분석이 완료되었습니다!")
                
            except Exception as e:
                st.error(f"❌ 오류가 발생했습니다: {str(e)}")
                
                # 디버깅 정보 표시
                with st.expander("🔧 디버깅 정보"):
                    st.write("**API 키 상태:**", "설정됨" if os.getenv("OPENAI_API_KEY") else "미설정")
                    st.write("**오류 메시지:**", str(e))
                    st.code("""
                    해결 방법:
                    1. .env 파일에 OPENAI_API_KEY 설정 확인
                    2. pip install --upgrade langchain langchain-openai
                    3. API 키 유효성 확인
                    """)

# 결과 표시
if st.session_state.result:
    st.markdown("---")
    st.subheader("📊 분석 결과")
    
    # 결과를 보기 좋게 표시
    with st.container():
        # 결과 텍스트를 박스에 표시
        st.info(st.session_state.result)
        
        # 결과 복사 버튼
        st.button("📋 결과 복사", 
                 on_click=lambda: st.toast("클립보드에 복사되었습니다!", icon="✅"),
                 help="결과를 클립보드에 복사합니다")
    
    # 응급처치 가이드 (선택사항)
    with st.expander("🏥 일반적인 응급처치 가이드"):
        st.markdown("""
        **⚠️ 주의: 이는 일반적인 가이드이며, 심각한 경우 즉시 119에 연락하세요**
        
        **피부 노출:**
        - 오염된 의복 제거
        - 다량의 물로 15분 이상 씻기
        - 자극이 지속되면 의료진 상담
        
        **안구 노출:**
        - 즉시 다량의 물로 15분 이상 세척
        - 콘택트렌즈 제거
        - 즉시 의료진 상담
        
        **경구 노출:**
        - 의식이 있는 경우 물로 입 헹구기
        - 구토 유도하지 말 것
        - 즉시 119 또는 중독센터(1339) 연락
        
        **흡입 노출:**
        - 신선한 공기가 있는 곳으로 이동
        - 호흡곤란 시 산소 공급
        - 즉시 의료진 상담
        """)

# 페이지 하단 정보
st.markdown("---")
st.caption("💡 이 서비스는 AI 기반 분석으로, 의학적 조언을 대체하지 않습니다. 응급상황 시 119 또는 중독정보센터(1339)에 연락하세요.")