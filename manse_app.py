# 파일 역할: manse_app.py 와와
# 이 파일은 Streamlit 라이브러리를 사용하여 웹 애플리케이션의 사용자 인터페이스(UI)를 생성하고 관리합니다.
# 사용자의 입력을 받고, 그 입력에 따라 utils.py와 constants.py의 기능을 호출하여 만세력 정보를 계산하고 결과를 화면에 표시합니다.
# 애플리케이션의 메인 실행 파일입니다.

import streamlit as st
from datetime import datetime, timedelta, time
import json
import utils  # 데이터 처리 및 만세력 계산 함수들이 들어있는 모듈
import constants  # 앱 전체에서 사용되는 상수(고정값)들이 들어있는 모듈

# --- 기본 설정값 정의 ---
# 인쇄 설정의 최초 기본값을 정의합니다. settings.json 파일이 없을 때 이 값이 사용됩니다.
DEFAULT_SETTINGS = {
    "p_b_top": 32.0, "p_b_left": 140.0,
    "p_s_top": 51.0, "p_s_left": 21.0,
    "p_a_top": 78.0, "p_a_left": 47.0,
    "f_b_size": 14.0, "f_s_size": 20.0, "f_a_size": 14.0
}

# --- 설정 저장 함수 ---
def save_current_settings():
    """
    st.session_state에서 현재 설정 값을 읽어 파일에 저장합니다.
    """
    # DEFAULT_SETTINGS의 키들을 기준으로 st.session_state에서 현재 설정값들을 가져와 딕셔너리를 만듭니다.
    current_settings = {key: st.session_state[key] for key in DEFAULT_SETTINGS.keys()}
    utils.save_settings(current_settings)

# --- Streamlit 페이지 설정 ---
st.set_page_config(page_title="만세력 조회", layout="centered")

# --- 커스텀 CSS 스타일 ---
# Streamlit 위젯의 기본 디자인을 수정하여 첨부된 이미지와 유사하게 만듭니다.
st.markdown("""
<style>
/* 입력 필드, 선택 상자 기본 스타일 */
div[data-baseweb="form-control"] > div {
    border-radius: 10px !important;
    border: 1px solid #E0E0E0 !important;
}
/* 선택 상자의 화살표 아이콘 색상 */
div[data-baseweb="select"] > div > div > svg {
    color: #333 !important;
}
/* 버튼 스타일 */
.stButton>button {
    border-radius: 10px !important;
    border: 1px solid #E0E0E0 !important;
    background-color: #FFFFFF !important;
    color: #333 !important;
    width: 100%;
}
.stButton>button:hover {
    border-color: #007bff !important;
    color: #007bff !important;
}
/* 라디오 버튼 간격 조정 */
div[role="radiogroup"] > div {
    gap: 15px;
}
</style>
""", unsafe_allow_html=True)


# --- 애플리케이션 제목 및 설명 ---
st.title("개인 정보 입력")
st.write("아래에 생년월일 정보를 입력해주세요.")
st.write("") # 여백

# --- 데이터 로딩 ---
df = utils.load_data()

# --- 메인 애플리케이션 로직 ---
if df is not None:
    # --- 설정 불러오기 및 session_state 초기화 ---
    settings = utils.load_settings(DEFAULT_SETTINGS)
    for key, value in settings.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if 'result_data' not in st.session_state:
        st.session_state.result_data = {}
    
    # 인쇄 버튼을 제어하기 위한 상태 변수
    if 'do_print' not in st.session_state:
        st.session_state.do_print = False
    
    # 인쇄 컴포넌트를 매번 새롭게 렌더링하기 위한 카운터
    if 'print_counter' not in st.session_state:
        st.session_state.print_counter = 0

    # --- 탭(Tab) 생성 ---
    tab1, tab2, tab3 = st.tabs(["만세력 조회 및 결과", "인쇄 설정", "피드백"])

    # --- '인쇄 설정' 탭 ---
    with tab2:
        st.subheader("인쇄 위치 조정 (mm 단위)")
        st.caption("A4 용지 기준, 좌측 상단 모서리로부터의 거리입니다.")
        pos_col1, pos_col2 = st.columns(2)
        with pos_col1:
            st.number_input("생년월일 (상단)", key="p_b_top", step=1.0, format="%.1f")
            st.number_input("만세력 (상단)", key="p_s_top", step=1.0, format="%.1f")
            st.number_input("나이/월주 정보 (상단)", key="p_a_top", step=1.0, format="%.1f")
        with pos_col2:
            st.number_input("생년월일 (좌측)", key="p_b_left", step=1.0, format="%.1f")
            st.number_input("만세력 (좌측)", key="p_s_left", step=1.0, format="%.1f")
            st.number_input("나이/월주 정보 (좌측)", key="p_a_left", step=1.0, format="%.1f")

        st.markdown("---")
        st.subheader("인쇄 글자 크기 조정 (pt 단위)")
        font_col1, font_col2, font_col3 = st.columns(3)
        with font_col1:
            st.number_input("생년월일", key="f_b_size", step=1.0, format="%.1f")
        with font_col2:
            st.number_input("만세력", key="f_s_size", step=1.0, format="%.1f")
        with font_col3:
            st.number_input("나이/월주 정보", key="f_a_size", step=1.0, format="%.1f")

        st.markdown("---")
        
        # 버튼들을 한 줄에 배치하고 간격을 줍니다.
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("설정 저장하기", key="save_settings_btn"):
                save_current_settings()
                st.toast("설정이 저장되었습니다.", icon="💾")

        with btn_col2:
            if st.button("설정 적용하여 인쇄하기", key="print_in_settings_tab"):
                if st.session_state.result_data:
                    st.session_state.do_print = True
                    st.session_state.print_counter += 1
                else:
                    st.toast("먼저 '만세력 조회 및 결과' 탭에서 데이터를 조회해주세요.", icon="⚠️")


    # --- '만세력 조회 및 결과' 탭 ---
    with tab1:
        # --- UI Helper Function ---
        def create_labeled_input(label, widget_fn, widget_args=None, widget_kwargs=None):
            """라벨과 입력 위젯을 한 줄에 생성하는 헬퍼 함수"""
            if widget_args is None: widget_args = []
            if widget_kwargs is None: widget_kwargs = {}
            
            cols = st.columns([1, 2.5])
            with cols[0]:
                st.markdown(f"<div style='height: 38px; display: flex; align-items: center;'>{label}</div>", unsafe_allow_html=True)
            with cols[1]:
                return widget_fn(*widget_args, **widget_kwargs)

        # --- 사용자 입력 필드 ---
        # 각 입력 항목을 라벨과 입력 필드로 구성된 행으로 재구성합니다.
        
        # 1. 생년월일
        cols = st.columns([1, 2.5]) # 라벨과 입력 필드의 비율 조정
        with cols[0]:
            st.markdown("<div style='height: 38px; display: flex; align-items: center;'>생년월일</div>", unsafe_allow_html=True)
        birth_date_str = cols[1].text_input("생년월일", placeholder="예: 19000101", label_visibility="collapsed")

        # 2. 시간
        time_cols = st.columns([1, 1.25, 1.25])
        time_cols[0].markdown("<div style='height: 38px; display: flex; align-items: center;'>시간</div>", unsafe_allow_html=True)
        time_input_method = time_cols[1].radio("시간 입력 방식", ('직접 입력', '12지시'), horizontal=True, label_visibility="collapsed")
        if time_input_method == '12지시':
            birth_time_option = time_cols[2].selectbox("12지시", options=constants.JIJI_OPTIONS, label_visibility="collapsed")
            birth_time_str_direct = ''
        else:
            birth_time_str_direct = time_cols[2].text_input("직접 입력", placeholder="숫자 네자리를 넣어주세요", max_chars=4, label_visibility="collapsed")
            birth_time_option = '시간 선택 안 함'

        # 3. 달력 종류
        cols = st.columns([1, 2.5])
        with cols[0]:
            st.markdown("<div style='height: 42px; display: flex; align-items: center;'>달력 종류</div>", unsafe_allow_html=True)
        with cols[1]:
            cal_type = st.radio("달력 종류", ("양력", "음력(평달)", "음력(윤달)"), horizontal=True, label_visibility="collapsed")

        # 4. 혈액형
        cols = st.columns([1, 2.5])
        with cols[0]:
            st.markdown("<div style='height: 42px; display: flex; align-items: center;'>혈액형</div>", unsafe_allow_html=True)
        with cols[1]:
            inner_cols = st.columns([4, 1])
            with inner_cols[0]:
                blood_type_base = st.radio("혈액형", ("선택 안함", "A형", "B형", "O형", "AB형"), horizontal=True, label_visibility="collapsed")
            with inner_cols[1]:
                 # st.radio와 st.checkbox의 기본 세로 정렬이 달라 높이를 맞추기 위해 상단에 여백(padding)을 추가합니다.
                 st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                 is_rh_minus = st.checkbox("Rh-")
        
        # 5. 출생 지역
        cols = st.columns([1, 2.5])
        with cols[0]:
            st.markdown("<div style='height: 38px; display: flex; align-items: center;'>출생 지역</div>", unsafe_allow_html=True)
        with cols[1]:
            region_options = ["선택 안함"] + list(constants.BIRTH_REGIONS.keys())
            birth_region = st.selectbox("출생 지역", options=region_options, label_visibility="collapsed")

        # 오류 메시지를 표시할 컨테이너
        error_container = st.empty()
        
        # --- 조회 및 인쇄 버튼 ---
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("만세력 정보 조회하기", use_container_width=True):
                # 버튼을 누르면 이전 오류 메시지를 지웁니다.
                error_container.empty()
                
                # utils.py에 새로 만든 함수를 호출하여 결과와 오류 메시지를 한 번에 받습니다.
                result_data, error_msg = utils.calculate_manse_info(
                    df=df,
                    birth_date_str=birth_date_str,
                    time_input_method=time_input_method,
                    birth_time_str_direct=birth_time_str_direct,
                    birth_time_option=birth_time_option,
                    cal_type=cal_type,
                    birth_region=birth_region,
                    blood_type_base=blood_type_base,
                    is_rh_minus=is_rh_minus
                )

                if error_msg:
                    error_container.error(error_msg)
                    st.session_state.result_data = {}
                else:
                    st.session_state.result_data = result_data
        
        with btn_col2:
            if st.button("인쇄하기", use_container_width=True):
                if st.session_state.result_data:
                    st.session_state.do_print = True # 인쇄 트리거 활성화
                    st.session_state.print_counter += 1 # 카운터 증가
                else:
                    st.toast("먼저 '만세 조회 및 결과' 탭에서 데이터를 조회해주세요.", icon="⚠️")

        # --- 조회 결과 표시 ---
        if st.session_state.result_data:
            st.markdown("---")
            data = st.session_state.result_data
            
            # 혈액형 정보가 있을 때만 표시되도록 수정합니다.
            blood_type_str = f"**혈액형**: {data.get('blood_type', '')}" if data.get('blood_type') else ""
            display_items = [
                f"**생년월일**: {data.get('birth_date', '')}", 
                f"**나이**: {data.get('age', '')}세"
            ]
            if blood_type_str:
                display_items.append(blood_type_str)

            st.write(" | ".join(display_items))

            st.markdown("---")
            pillars = data.get("pillars", {})
            display_order = ["시주(時柱)", "일주(日柱)", "월주(月柱)", "연주(年柱)"]
            pillars_to_display = {title: pillars[title] for title in display_order if title in pillars}
            cols = st.columns(len(pillars_to_display))
            for i, (title, ganjee) in enumerate(pillars_to_display.items()):
                with cols[i]:
                    st.subheader(title)
                    st.markdown(f"<h2 style='text-align: center;'>{ganjee[0]}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<h2 style='text-align: center;'>{ganjee[1]}</h2>", unsafe_allow_html=True)

    # --- 피드백 탭 ---
    with tab3:
        st.subheader("피드백 및 개선사항")
        st.write("앱 사용 중 발견한 오류나 개선 아이디어를 자유롭게 남겨주세요.")
        
        # 새로운 피드백 입력
        feedback_text = st.text_area("내용 입력:", height=150, placeholder="여기에 내용을 입력하세요...")
        
        if st.button("피드백 제출", key="submit_feedback", use_container_width=True):
            if utils.save_feedback(feedback_text):
                st.toast("소중한 의견 감사합니다!", icon="💌")
                st.rerun()
            else:
                st.toast("내용을 입력해주세요.", icon="⚠️")

        st.markdown("---")

        # 저장된 피드백 목록 표시
        st.subheader("피드백 기록")
        feedback_list = utils.load_feedback()
        
        if not feedback_list:
            st.info("아직 기록된 피드백이 없습니다.")
        else:
            for feedback in feedback_list:
                timestamp = feedback['timestamp']
                text = feedback['text']
                status = feedback['status']
                
                # 상태에 따라 아이콘과 색상을 다르게 표시합니다.
                icon = "✅" if status == 'resolved' else "📝"
                expander_title = f"{icon} {timestamp} - {text[:40]}{'...' if len(text) > 40 else ''}"
                
                with st.expander(expander_title):
                    st.markdown(f"**내용:**\n```\n{text}\n```")
                    
                    # 상태 변경 버튼
                    if status == 'open':
                        if st.button("해결로 표시", key=f"resolve_{timestamp}", use_container_width=True):
                            utils.update_feedback_status(timestamp, 'resolved')
                            st.rerun()
                    else: # status == 'resolved'
                        if st.button("다시 열기", key=f"reopen_{timestamp}", use_container_width=True):
                            utils.update_feedback_status(timestamp, 'open')
                            st.rerun()


    # --- 인쇄 로직 실행 ---
    # 이 부분은 탭 밖에 위치하여 어느 탭에서든 인쇄 버튼을 누르면 실행됩니다.
    if st.session_state.get('do_print', False):
        # 인쇄할 데이터가 있는지 다시 한번 확인합니다.
        if st.session_state.result_data:
            positions = {
                "birth_date_top": st.session_state.p_b_top, "birth_date_left": st.session_state.p_b_left,
                "manse_grid_top": st.session_state.p_s_top, "manse_grid_left": st.session_state.p_s_left,
                "age_info_top": st.session_state.p_a_top, "age_info_left": st.session_state.p_a_left
            }
            font_sizes = {
                "birth_date_fs": st.session_state.f_b_size,
                "manse_grid_fs": st.session_state.f_s_size,
                "age_info_fs": st.session_state.f_a_size
            }
            print_html = utils.generate_print_html(st.session_state.result_data, positions, font_sizes)
            safe_html = json.dumps(print_html)
            js_code = f"""
                <iframe id="print_iframe" style="display:none;"></iframe>
                <script>
                    // Print Counter: {st.session_state.print_counter}
                    const iframe = document.getElementById('print_iframe');
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    doc.open();
                    doc.write({safe_html});
                    doc.close();
                    setTimeout(() => {{
                        iframe.contentWindow.focus();
                        iframe.contentWindow.print();
                    }}, 500);
                </script>
            """
            st.components.v1.html(js_code, height=0)
            st.toast("인쇄 창을 실행합니다...", icon="🖨️")
            
            # 인쇄 컴포넌트를 렌더링한 후, 트리거를 리셋합니다.
            st.session_state.do_print = False
