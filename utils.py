# 파일 역할: utils.py
# 이 파일은 애플리케이션의 핵심 로직을 담당하는 함수들을 모아놓은 '유틸리티' 또는 '헬퍼' 모듈입니다.
# 데이터베이스 연결, 데이터 처리, 만세력 계산, HTML 생성 등 복잡하고 반복적인 작업들을 함수로 분리하여
# 메인 파일(manse_app.py)의 코드를 간결하고 이해하기 쉽게 만듭니다.

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from datetime import datetime, timedelta, time
import os
from constants import CHEONGAN, JIJI # constants.py 파일에서 천간, 지지 리스트를 가져옵니다.

# --- 1. 데이터 로딩 및 전처리 ---
# '@st.cache_data'는 Streamlit의 강력한 기능으로, 함수의 결과를 메모리에 저장(캐싱)합니다.
# 이렇게 하면 함수가 동일한 입력으로 다시 호출될 때, 복잡한 계산을 반복하는 대신 저장된 결과를 즉시 반환하여 앱 속도를 크게 향상시킵니다.
# 데이터베이스 파일을 읽는 것처럼 비용이 큰 작업에 매우 유용합니다.
@st.cache_data
def load_data(db_path='manse_db.sqlite'):
    """
    SQLite 데이터베이스에서 만세력 데이터를 불러와 Pandas DataFrame으로 변환하고,
    컬럼 이름을 더 이해하기 쉬운 이름으로 변경합니다.
    데이터베이스 파일이 없거나 오류가 발생하면 None을 반환하고 에러 메시지를 표시합니다.
    """
    try:
        # 데이터베이스에 연결합니다.
        conn = sqlite3.connect(db_path)
        # SQL 쿼리를 실행하여 'calenda_data' 테이블의 모든 데이터를 가져옵니다.
        query = "SELECT * FROM calenda_data"
        df = pd.read_sql_query(query, conn)
        # 데이터베이스 연결을 닫습니다.
        conn.close()

        # 원본 컬럼 이름(예: 'cd_sgi')을 새로운 이름(예: 'year_seogi')으로 변경하기 위한 딕셔너리입니다.
        rename_dict = {
            'cd_sgi': 'year_seogi', 'cd_sy': 'solar_year', 'cd_sm': 'solar_month',
            'cd_sd': 'solar_day', 'cd_ly': 'lunar_year', 'cd_lm': 'lunar_month',
            'cd_ld': 'lunar_day', 'cd_is_yun': 'is_leap',  # 윤달 정보 컬럼
            'cd_hyganjee': 'year_ganjee_hj', 'cd_kyganjee': 'year_ganjee_kr',
            'cd_hmganjee': 'month_ganjee_hj', 'cd_kmganjee': 'month_ganjee_kr',
            'cd_hdganjee': 'day_ganjee_hj', 'cd_kdganjee': 'day_ganjee_kr',
            'holiday': 'is_holiday'
        }
        # DataFrame의 컬럼 이름을 변경합니다. 'inplace=True'는 원본 DataFrame을 직접 수정하라는 의미입니다.
        df.rename(columns=rename_dict, inplace=True)
        
        # 'is_leap' 컬럼이 없는 구버전 DB 파일을 대비한 예외 처리입니다.
        # 만약 'is_leap' 컬럼이 없다면, 모든 값을 '평'으로 채운 새로운 컬럼을 만듭니다.
        if 'is_leap' not in df.columns:
            df['is_leap'] = '평'

        # 날짜 관련 컬럼들의 데이터 타입을 문자열에서 숫자(정수)로 변환합니다.
        # 'errors='coerce'' 옵션은 변환 중 오류가 발생하면 해당 값을 NaT(Not a Time)으로 처리합니다.
        for col in ['solar_year', 'solar_month', 'solar_day', 'lunar_year', 'lunar_month', 'lunar_day']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 처리된 DataFrame을 반환합니다.
        return df
    except Exception as e:
        # 데이터 로딩 중 어떤 종류의 오류든 발생하면, 사용자에게 에러 메시지를 보여줍니다.
        st.error(f"데이터베이스 파일을 불러오는 데 실패했습니다: {e}")
        st.info("'manse_app.py'와 'manse_db.sqlite' 파일이 같은 폴더에 있는지 확인해주세요.")
        # 실패 시 None을 반환하여 메인 앱에서 데이터가 없음을 알 수 있게 합니다.
        return None

# --- 2. 핵심 기능 함수 ---

def get_time_jiji_from_datetime(birth_dt):
    """
    태어난 시간(datetime 객체)을 기준으로 12지지(자시, 축시 등) 중 해당하는 시간의 지지를 반환합니다.
    예: 12시 30분 -> '午' (오)
    """
    # 시간대와 지지를 매핑하는 리스트. (시작 시간(HHMM), 지지)
    TIME_JIJI_MAP = [
        (130, "丑"), (330, "寅"), (530, "卯"), (730, "辰"),
        (930, "巳"), (1130, "午"), (1330, "未"), (1530, "申"),
        (1730, "酉"), (1930, "戌"), (2130, "亥"), (2330, "子")
    ]

    # 시간을 '시*100 + 분' 형태의 숫자로 변환하여 비교하기 쉽게 만듭니다. 예: 11시 30분 -> 1130
    time_val = birth_dt.hour * 100 + birth_dt.minute

    # 23:30 이후는 다음 날의 자시(子)에 해당
    if time_val >= 2330:
        return "子"

    # 시간대 맵을 순회하며 해당하는 지지를 찾습니다.
    for limit, jiji in TIME_JIJI_MAP:
        if time_val < limit:
            return jiji

    # 01:30 이전은 자시(子)에 해당
    return "子"

def get_time_cheongan(day_ganjee_hj, time_jiji):
    """
    일주(日柱)의 천간과 태어난 시간의 지지(時支)를 사용하여 시주(時柱)의 천간(時干)을 계산합니다.
    이것은 '시두법(時頭法)'이라는 만세력 명리학의 원리를 따릅니다.
    """
    # 입력값이 유효한지 확인합니다. 일주(예: '甲子')와 시지(예: '午')가 정확해야 합니다.
    if not (isinstance(day_ganjee_hj, str) and len(day_ganjee_hj) == 2 and time_jiji in JIJI):
        return None
    
    day_cheon = day_ganjee_hj[0] # 일주의 천간 (예: '甲子' -> '甲')
    try:
        # 천간과 지지의 순서(인덱스)를 찾습니다.
        day_cheon_index = CHEONGAN.index(day_cheon)
        time_jiji_index = JIJI.index(time_jiji)
    except ValueError:
        return None # 리스트에 없는 글자일 경우 오류 방지

    # 시두법 공식: 일간에 따라 자시(子時)의 천간이 정해집니다.
    # 예: 일간이 甲이나 己이면 자시의 천간은 甲(甲子時)부터 시작합니다.
    start_cheon_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 0, 6: 2, 7: 4, 8: 6, 9: 8} # 甲(0), 己(5) -> 甲(0) ...
    start_cheon_index = start_cheon_map.get(day_cheon_index)

    # 자시의 천간에서부터 태어난 시간의 지지 순서만큼 더해 시간의 천간을 구합니다.
    # 10으로 나눈 나머지를 구하는 것은 천간이 10개이므로 순환시키기 위함입니다.
    time_cheon_index = (start_cheon_index + time_jiji_index) % 10
    return CHEONGAN[time_cheon_index] # 계산된 인덱스에 해당하는 천간을 반환합니다.

def validate_date(date_str):
    """
    사용자가 입력한 8자리 날짜 문자열(예: "19730819")이 유효한 날짜인지 검사합니다.
    유효하면 datetime 객체로 변환하여 반환하고, 아니면 에러 메시지를 반환합니다.
    """
    if not (len(date_str) == 8 and date_str.isdigit()):
        return None, "생년월일은 8자리 숫자로 입력해주세요. (예: 19730819)"
    try:
        # 문자열을 datetime 객체로 변환 시도
        return datetime.strptime(date_str, '%Y%m%d'), None
    except ValueError:
        # 변환 실패 시 (예: "20230230"처럼 없는 날짜) 에러 메시지 반환
        return None, "입력하신 날짜가 유효하지 않습니다. 다시 확인해주세요."

def calculate_manse_info(df, birth_date_str, time_input_method, birth_time_str_direct, birth_time_option, cal_type, birth_region, blood_type_base, is_rh_minus):
    """사용자 입력을 바탕으로 만세력 정보를 계산하고 결과 딕셔너리 또는 오류 메시지를 반환합니다."""
    from constants import BIRTH_REGIONS, JIJI_TO_ZODIAC

    date_obj, error_msg = validate_date(birth_date_str)
    if error_msg:
        return None, error_msg

    is_time_entered = False
    birth_time_for_calc = None

    if time_input_method == '직접 입력':
        if birth_time_str_direct:
            if len(birth_time_str_direct) == 4 and birth_time_str_direct.isdigit():
                try:
                    hour, minute = int(birth_time_str_direct[:2]), int(birth_time_str_direct[2:])
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        return None, "시간을 0000에서 2359 사이의 유효한 값으로 입력해주세요."
                    birth_time_for_calc = time(hour, minute)
                    is_time_entered = True
                except ValueError:
                    return None, "시간을 4자리 숫자로 정확하게 입력해주세요."
            # 시간이 비어있으면 그냥 넘어감 (시간 입력 안함으로 처리)
    elif time_input_method == '12지시':
        if birth_time_option != '시간 선택 안 함':
            is_time_entered = True

    true_solar_dt = None
    if is_time_entered:
        region_offset = BIRTH_REGIONS.get(birth_region, 0)
        if time_input_method == '12지시':
            try:
                time_str = birth_time_option.split('(')[1].split('~')[0]
                hour, minute = map(int, time_str.split(':'))
                base_dt = datetime.combine(date_obj, time(hour, minute))
                true_solar_dt = base_dt + timedelta(minutes=region_offset)
            except (IndexError, ValueError):
                is_time_entered = False # 파싱 실패 시 시간 미입력으로 간주
        elif birth_time_for_calc: # 직접 입력
            base_dt = datetime.combine(date_obj, birth_time_for_calc)
            true_solar_dt = base_dt + timedelta(minutes=region_offset)

    lookup_date = date_obj
    lookup_year, lookup_month, lookup_day = lookup_date.year, lookup_date.month, lookup_date.day
    query_map = {
        "양력": (df['solar_year'] == lookup_year) & (df['solar_month'] == lookup_month) & (df['solar_day'] == lookup_day),
        "음력(평달)": (df['lunar_year'] == lookup_year) & (df['lunar_month'] == lookup_month) & (df['lunar_day'] == lookup_day) & (df['is_leap'] != '윤'),
        "음력(윤달)": (df['lunar_year'] == lookup_year) & (df['lunar_month'] == lookup_month) & (df['lunar_day'] == lookup_day) & (df['is_leap'] == '윤')
    }
    result_row = df[query_map[cal_type]]

    if result_row.empty:
        return None, "데이터베이스에서 해당 날짜 정보를 찾을 수 없습니다. (지원 범위: 1900년 ~ 2050년)"

    result = result_row.iloc[0]
    korean_age = datetime.now().year - result['solar_year'] + 1
    pillars = {
        "연주(年柱)": result['year_ganjee_hj'],
        "월주(月柱)": result['month_ganjee_hj'],
        "일주(日柱)": result['day_ganjee_hj'],
    }

    if is_time_entered and true_solar_dt is not None:
        # 자시(23:30-01:29)는 날짜가 바뀔 수 있으므로, 시주 계산 시 실제 태어난 날의 일주를 사용해야 함
        day_ganjee_to_use = result['day_ganjee_hj']
        # 23:30 이후 출생 시, 일주 간지는 다음날의 것을 사용해야 할 수 있으나, 만세력의 복잡한 규칙(절기 기준)이 있어 여기서는 조회된 날의 일주를 그대로 사용합니다.
        # (정확도를 더 높이려면 야자시/조자시 구분이 필요)
        time_jiji = get_time_jiji_from_datetime(true_solar_dt)
        if time_jiji:
            time_cheon = get_time_cheongan(day_ganjee_to_use, time_jiji)
            if time_cheon:
                pillars["시주(時柱)"] = time_cheon + time_jiji

    blood_type = ""
    if blood_type_base != "선택 안함":
        blood_type = f"{blood_type_base}(Rh-)" if is_rh_minus else blood_type_base

    result_data = {
        "birth_date": date_obj.strftime('%y.%m.%d'),
        "age": korean_age,
        "blood_type": blood_type,
        "zodiac": JIJI_TO_ZODIAC.get(pillars.get("연주(年柱)", "  ")[1], ""),
        "pillars": pillars,
        "cal_type": cal_type
    }
    return result_data, None


# --- 3. 설정 파일 처리 ---

import json

def save_settings(settings, path='settings.json'):
    """
    인쇄 설정값(딕셔너리)을 JSON 파일로 저장합니다.
    """
    try:
        # 파일을 쓰기 모드('w')로 열고, UTF-8 인코딩을 사용합니다.
        # 'indent=4'는 JSON 파일을 사람이 보기 좋게 4칸 들여쓰기로 저장하라는 옵션입니다.
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        # 파일 저장 중 오류 발생 시, 사용자에게 알려줍니다.
        st.error(f"설정을 저장하는 데 실패했습니다: {e}")

def load_settings(default_settings, path='settings.json'):
    """
    JSON 파일에서 인쇄 설정값을 불러옵니다. 파일이 없으면 기본 설정값을 반환합니다.
    """
    # 설정 파일이 존재하는지 확인합니다.
    if os.path.exists(path):
        try:
            # 파일을 읽기 모드('r')로 엽니다.
            with open(path, 'r', encoding='utf-8') as f:
                # JSON 파일의 내용을 읽어 파이썬 딕셔너리로 변환하여 반환합니다.
                return json.load(f)
        except Exception as e:
            # 파일 읽기 중 오류 발생 시, 사용자에게 알리고 기본값을 사용합니다.
            st.error(f"설정 파일을 불러오는 데 실패했습니다: {e}")
            return default_settings
    else:
        # 파일이 존재하지 않으면, 미리 정의된 기본 설정값을 반환합니다.
        return default_settings

# --- 4. 인쇄용 HTML 생성 ---

def generate_print_html(data, positions, font_sizes):
    """
    만세력 결과 데이터와 위치/크기 설정값을 바탕으로 인쇄용 HTML 문서를 동적으로 생성합니다.
    """
    # 전달받은 데이터들을 각 변수에 할당하여 코드 가독성을 높입니다.
    birth_date = data.get('birth_date', '')
    cal_type_char = '(+)' if data.get('cal_type') == '양력' else '(-)'
    age = data.get('age', '')
    
    pillars = data.get('pillars', {})
    
    # 월주가 있으면 두 번째 글자(지지)만 사용하고, 없으면 빈 문자열로 처리합니다.
    month_jiji = pillars.get('월주(月柱)', '  ')[1] if '월주(月柱)' in pillars else ''
    
    blood_type = data.get('blood_type', '')

    # --- HTML 구조 생성 ---
    # 절대 위치(absolute positioning)를 사용하여 각 정보 블록을 A4 용지 위의 특정 좌표에 배치합니다.
    # 위치와 글자 크기는 '인쇄 설정' 탭에서 사용자가 조정한 값이 mm와 pt 단위로 적용됩니다.
    
    # 1. 생년월일 정보 HTML
    birth_date_html = f"""
    <div style="position: absolute; top: {positions['birth_date_top']}mm; left: {positions['birth_date_left']}mm; font-size: {font_sizes['birth_date_fs']}pt; letter-spacing: 1px;">
        {birth_date}{cal_type_char}
    </div>
    """
    
    # 2. 만세력 정보 HTML
    # 표시할 만세력 기둥들을 순서대로 정렬합니다. 시주가 없으면 3개만 표시됩니다.
    display_order = ["시주(時柱)", "일주(日柱)", "월주(月柱)", "연주(年柱)"]
    pillars_to_display = {title: pillars[title] for title in display_order if title in pillars}
    
    # 만세력 8글자를 윗줄(천간)과 아랫줄(지지)로 분리합니다.
    top_row_chars = [ganjee[0] for ganjee in pillars_to_display.values()]
    bottom_row_chars = [ganjee[1] for ganjee in pillars_to_display.values()]
    
    # 각 줄의 글자들을 HTML div 태그로 감싸줍니다. padding 값을 0.1em으로 설정하여 간격을 좁힙니다.
    top_row_html = "".join([f"<div style='padding: 0 0.1em;'>{char}</div>" for char in top_row_chars])
    bottom_row_html = "".join([f"<div style='padding: 0 0.1em;'>{char}</div>" for char in bottom_row_chars])

    manse_grid_html = f"""
    <div style="position: absolute; top: {positions['manse_grid_top']}mm; left: {positions['manse_grid_left']}mm; font-size: {font_sizes['manse_grid_fs']}pt; font-family: 'Malgun Gothic', sans-serif; text-align: center; line-height: 1.2;">
        <div style="display: flex; justify-content: center;">{top_row_html}</div>
        <div style="display: flex; justify-content: center;">{bottom_row_html}</div>
    </div>
    """
    
    # 3. 나이, 월주 지지, 혈액형 정보 HTML
    # 혈액형 정보가 있을 때만 ' - 혈액형' 부분을 추가합니다.
    age_info_parts = [f"{age}세", month_jiji]
    if blood_type:
        age_info_parts.append(blood_type)
    age_info_text = " - ".join(filter(None, age_info_parts)) # 빈 항목은 제외하고 ' - '로 연결

    age_info_html = f"""
    <div style="position: absolute; top: {positions['age_info_top']}mm; left: {positions['age_info_left']}mm; font-size: {font_sizes['age_info_fs']}pt;">
        {age_info_text}
    </div>
    """

    # --- 전체 HTML 문서 조합 ---
    # 생성된 각 정보 블록 HTML을 기본 HTML 양식에 삽입하여 최종 문서를 완성합니다.
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>만세력 정보 인쇄</title>
        <style>
            /* A4 용지 크기와 여백을 설정합니다. */
            @page {{
                size: A4;
                margin: 0;
            }}
            body {{
                margin: 0;
                padding: 0;
                width: 210mm;
                height: 297mm;
                font-family: 'Malgun Gothic', sans-serif;
            }}
        </style>
    </head>
    <body>
        {birth_date_html}
        {manse_grid_html}
        {age_info_html}
    </body>
    </html>
    """
    return full_html

# --- 5. 피드백 저장 및 불러오기 함수 ---
FEEDBACK_FILE = 'feedback.json'

def save_feedback(feedback_text):
    """
    사용자가 입력한 피드백을 JSON 파일에 객체 형태로 저장합니다.
    """
    if feedback_text.strip():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_feedback = {
            'timestamp': timestamp,
            'text': feedback_text.strip(),
            'status': 'open'  # 'open' 또는 'resolved'
        }
        
        all_feedback = load_feedback()
        all_feedback.insert(0, new_feedback)  # 새 피드백을 맨 앞에 추가
        
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_feedback, f, indent=4, ensure_ascii=False)
        return True
    return False

def load_feedback():
    """
    JSON 형식의 피드백 파일을 읽어와 리스트로 반환합니다.
    """
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] # 파일이 비어있거나 형식이 잘못된 경우 빈 리스트 반환
    return []

def update_feedback_status(timestamp, new_status):
    """
    특정 타임스탬프를 가진 피드백의 상태를 변경합니다.
    """
    all_feedback = load_feedback()
    for feedback in all_feedback:
        if feedback['timestamp'] == timestamp:
            feedback['status'] = new_status
            break
            
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_feedback, f, indent=4, ensure_ascii=False)
