import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import altair as alt
import os

FILE = "sleep_log.csv"
DATE_FILE = "current_date.txt"  # 가상 날짜 저장용


# -- 가상 날짜 초기화 및 세션 상태 관리 --
def load_and_init_current_date():
    if "current_date" not in st.session_state:
        d = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if os.path.exists(DATE_FILE):
            with open(DATE_FILE, "r") as f:
                d_str = f.read().strip()
                try:
                    d = datetime.strptime(d_str, "%Y-%m-%d")
                except ValueError:
                    st.sidebar.error(f"⚠️ 날짜 파일 '{DATE_FILE}' 읽기 오류: '{d_str}' 파싱 실패. 오늘 날짜로 초기화.")
        st.session_state.current_date = d
        save_current_date_to_file(d)  # 초기 로드 시 파일에 저장


# current_date를 파일에 저장하는 별도 함수
def save_current_date_to_file(d: datetime):
    try:
        with open(DATE_FILE, "w") as f:
            f.write(d.strftime("%Y-%m-%d"))  # 이 파일은 날짜만 저장해도 무방
        st.sidebar.success(f"현재 날짜 파일 저장 성공: {d.strftime('%Y-%m-%d')}")
    except IOError as e:
        st.sidebar.error(f"⚠️ 현재 날짜 파일 '{DATE_FILE}' 저장 오류: {e}")


# 앱 시작 시 current_date 로드 및 초기화
load_and_init_current_date()
current_date = st.session_state.current_date

# 🐛 **디버깅:** 현재 날짜 변수 값 확인
st.sidebar.subheader("현재 가상 날짜 상태")
st.sidebar.write(f"Loaded current_date (from session_state): {current_date.strftime('%Y-%m-%d (%A)')}")

# -- 데이터 파일 초기화 --
if not os.path.exists(FILE):
    df_init = pd.DataFrame(columns=["date", "sleep_start", "sleep_end"])
    df_init.to_csv(FILE, index=False)

# -- 타이틀 --
st.title("🛏️ 수면 시간 기록 및 분석기")

st.write(f"### 현재 날짜: {current_date.strftime('%Y-%m-%d (%A')}")

# -- 데이터 불러오기 및 초기 처리 (중요!) --
df = pd.read_csv(FILE)  # FILE 변수 사용

# 🐛 **디버깅:** 로드 직후 원본 'date' 컬럼 내용과 타입 확인
st.sidebar.subheader("로드 직후 'date' 컬럼 원본 상태")
st.sidebar.dataframe(df["date"])
st.sidebar.write(f"원본 'date' 컬럼 타입: {df['date'].dtype}")

# 🔧 날짜 강제 변환 + NaT 제거 + 복사 (✅ 매번 데이터 로드 후 즉시 실행)
# errors='coerce'는 변환할 수 없는 값을 NaT로 만듭니다.
# date 컬럼을 datetime으로 변환하되, 시간 정보가 없으면 00:00:00으로 설정됨
df["date"] = pd.to_datetime(df["date"], errors="coerce")
# NaT (Not a Time) 값은 제거합니다.
df = df[df["date"].notna()].copy()

# 🐛 **디버깅:** pd.to_datetime 적용 후 'date' 컬럼 상태 확인
st.sidebar.subheader("pd.to_datetime 적용 후 'date' 컬럼 상태")
st.sidebar.dataframe(df["date"])
st.sidebar.write(f"변환 후 'date' 컬럼 타입: {df['date'].dtype}")

# 🐛 **디버깅:** 로드된 전체 DataFrame 확인 (사이드바에 표시)
st.sidebar.subheader("1. 로드된 전체 데이터 (df)")
st.sidebar.dataframe(df)
st.sidebar.write(f"최종 'date' 컬럼 타입: {df['date'].dtype}")

# 문자열 포맷으로 바꾸기 (주로 '오늘 날짜 기록 중복 체크'에 사용)
st.sidebar.subheader("date_str_short 생성 전 df['date']")
st.sidebar.dataframe(df['date'])
df["date_str_short"] = df["date"].dt.strftime("%m-%d")
st.sidebar.subheader("date_str_short 생성 후 df")
st.sidebar.dataframe(df[["date", "date_str_short"]])

# -- 오늘 날짜 기록 중복 체크 --
today_str = current_date.strftime("%Y-%m-%d")  # 현재 앱의 날짜는 YYYY-MM-DD 형식
# df["date"]는 datetime 타입 (시간 포함)이므로, 비교를 위해 YYYY-MM-DD 형식으로 변환해야 함
if not df.empty and today_str in df["date"].dt.strftime("%Y-%m-%d").values:
    entered_today = True
else:
    entered_today = False

# -- 수면 시간 입력 --
st.subheader("📝 수면 시간 입력 (HH:MM 형식, 24시간제)")

start_input = st.text_input("취침 시각 (예: 23:30)", key="start_time")
end_input = st.text_input("기상 시각 (예: 07:00)", key="end_time")

if st.button("기록 저장하기"):
    if entered_today:
        st.warning("이미 오늘 날짜에 기록이 있습니다.")
    else:
        try:
            # 입력값 유효성 검사 (비어있는지 확인)
            if not start_input or not end_input:
                st.error("취침 시각과 기상 시각을 모두 입력해주세요.")
                st.stop()  # 함수 실행 중단

            # sleep_start_time = datetime.strptime(start_input, "%H:%M").time() # 사용되지 않음
            # sleep_end_time = datetime.strptime(end_input, "%H:%M").time() # 사용되지 않음

            # current_date는 이미 00:00:00으로 설정된 datetime 객체
            # 새로운 기록의 date 컬럼을 YYYY-MM-DD 00:00:00 형식으로 명시적으로 저장
            date_to_save = current_date.strftime("%Y-%m-%d 00:00:00")

            # 기록 추가
            new_row = pd.DataFrame(
                [[date_to_save, start_input, end_input]],  # YYYY-MM-DD 00:00:00 형식으로 저장
                columns=["date", "sleep_start", "sleep_end"]
            )

            # 🐛 **디버깅:** 병합 전의 DataFrame과 새로운 행 확인
            st.sidebar.subheader("2. 저장 전: 현재 데이터 (df) + 새 행 (new_row)")
            st.sidebar.dataframe(df)
            st.sidebar.dataframe(new_row)

            # df에 새로운 row를 추가합니다.
            df = pd.concat([df, new_row], ignore_index=True)

            # 🐛 **디버깅:** 병합 후의 DataFrame 확인
            st.sidebar.subheader("3. 저장 전: 병합된 데이터 (df)")
            st.sidebar.dataframe(df)

            # 변경된 DataFrame을 CSV 파일에 저장합니다.
            try:
                df.to_csv(FILE, index=False)
                st.success(f"{current_date.strftime('%Y-%m-%d')} 기록이 저장되었습니다.")

                # 🐛 **디버깅:** 파일 저장 직후, 저장된 파일의 내용을 다시 읽어 확인
                st.sidebar.subheader("4. 저장 후: CSV 파일 내용 확인")
                saved_df_check = pd.read_csv(FILE)
                st.sidebar.dataframe(saved_df_check)

            except IOError as e:
                st.error(f"파일 저장 중 오류가 발생했습니다: {e}. 파일 권한을 확인해주세요.")
                st.sidebar.error(f"IOError: {e}")
            except Exception as e:
                st.error(f"기록 저장 중 예상치 못한 오류가 발생했습니다: {e}")
                st.sidebar.error(f"저장 오류: {e}")

            st.rerun()  # 저장 후 앱 새로고침
        except ValueError:  # 시간을 잘못 입력했을 때의 오류를 더 구체적으로 잡습니다.
            st.error("시간 형식이 잘못되었습니다. HH:MM 형식으로 입력해주세요.")

st.markdown("---")


# -- 수면 시간 계산 함수 --
def calc_duration(row):
    try:
        # 입력된 sleep_start와 sleep_end는 문자열이므로 다시 파싱합니다.
        start_time_str = str(row["sleep_start"]).strip()
        end_time_str = str(row["sleep_end"]).strip()

        start = datetime.strptime(start_time_str, "%H:%M")
        end = datetime.strptime(end_time_str, "%H:%M")
        if end <= start:
            end += timedelta(days=1)
        duration = end - start
        return duration.total_seconds() / 60  # 분 단위
    except (ValueError, TypeError) as e:
        st.sidebar.error(f"⚠️ 수면 시간 계산 오류: "
                         f"날짜 '{row.get('date_for_chart', row.get('date', 'N/A'))}', "
                         f"취침 '{row.get('sleep_start')}' (타입: {type(row.get('sleep_start'))}, 변환 후: '{start_time_str}'), "
                         f"기상 '{row.get('sleep_end')}' (타입: {type(row.get('sleep_end'))}, 변환 후: '{end_time_str}') -> {e}")
        return None


if not df.empty:
    # sleep_minutes 컬럼 계산
    df["sleep_minutes"] = df.apply(calc_duration, axis=1)

    # 차트/분석에 사용할 날짜 문자열 컬럼 생성 (yyyy-mm-dd 형식)
    df["date_for_chart"] = df["date"].dt.strftime("%Y-%m-%d")

    # 필터링: 수면시간이 계산된 유효한 데이터만 사용
    df_valid = df[df["sleep_minutes"].notna()]

    # 🐛 **디버깅:** 유효한 데이터 (df_valid) 확인 (사이드바에 표시)
    st.sidebar.subheader("5. 유효한 데이터 (df_valid)")
    st.sidebar.dataframe(df_valid)

    if not df_valid.empty:
        df_valid["sleep_time_str"] = df_valid["sleep_minutes"].apply(lambda x: f"{int(x // 60)}:{int(x % 60):02d}")

        # 평균 수면 시간 계산 (기존과 동일)
        avg_minutes = df_valid["sleep_minutes"].mean()
        avg_hours = int(avg_minutes // 60)
        avg_min = int(avg_minutes % 60)

        st.subheader("📊 평균 수면 시간")
        st.write(f"**{avg_hours}시간 {avg_min}분**")


        # --- 새로운 추천 시각 계산 로직 ---

        # 1. 평균 취침 시각 계산
        # sleep_start 문자열을 분으로 변환
        def time_to_minutes(time_str):
            try:
                h, m = map(int, time_str.split(':'))
                # 자정을 넘는 취침 시각 (예: 23:00)을 다음 날로 간주하여 계산
                # 00:00 ~ 12:00 (정오)는 다음날로, 12:00 ~ 23:59는 당일로 처리
                if h >= 12:  # 오후 12시 (정오) 이후는 당일
                    return h * 60 + m
                else:  # 자정부터 오전 11시 59분까지는 다음 날 (24시간 + 해당 시간)
                    return (h + 24) * 60 + m
            except:
                return None  # 오류 발생 시 None 반환


        df_valid["sleep_start_minutes"] = df_valid["sleep_start"].apply(time_to_minutes)

        # 유효한 sleep_start_minutes만 사용하여 평균 계산
        avg_sleep_start_minutes = df_valid["sleep_start_minutes"].dropna().mean()

        # 평균 분을 다시 시간으로 변환
        # 24시간을 넘을 수 있으므로 % 1440 (24*60)으로 처리
        avg_sleep_start_hour = int((avg_sleep_start_minutes % 1440) // 60)
        avg_sleep_start_minute = int((avg_sleep_start_minutes % 1440) % 60)

        avg_sleep_start_time_obj = time(avg_sleep_start_hour, avg_sleep_start_minute)

        # 2. 추천 수면 시각 표시
        st.write(f"😴 추천 수면 시각 (평균 기반): **{avg_sleep_start_time_obj.strftime('%H:%M')}**")

        # 3. 추천 기상 시각 계산 및 표시
        # 평균 취침 시각 (datetime 객체로 변환) + 평균 수면 시간
        # 기준 날짜는 아무 날짜나 사용해도 무방 (시간 계산이므로)
        base_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        avg_sleep_start_datetime = base_datetime.replace(hour=avg_sleep_start_time_obj.hour,
                                                         minute=avg_sleep_start_time_obj.minute)

        rec_wake_time_datetime = avg_sleep_start_datetime + timedelta(minutes=avg_minutes)
        rec_wake_time = rec_wake_time_datetime.time()  # 시간 부분만 추출

        st.write(f"🌅 추천 기상 시각 (평균 기반): **{rec_wake_time.strftime('%H:%M')}**")

        # --- (기존 차트 및 요일별 평균 로직 유지) ---

        # 요일별 평균
        df_valid["weekday"] = df_valid["date"].dt.day_name()
        weekday_avg = df_valid.groupby("weekday")["sleep_minutes"].mean()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_avg = weekday_avg.reindex(weekday_order).dropna()

        if not weekday_avg.empty:
            st.subheader("📅 요일별 평균 수면 시간 (분)")
            weekday_chart = alt.Chart(weekday_avg.reset_index()).mark_bar().encode(
                x=alt.X("weekday", sort=weekday_order),
                y=alt.Y("sleep_minutes", title="평균 수면 시간 (분)"),
                tooltip=[alt.Tooltip("sleep_minutes", format=".1f")]
            ).properties(width=600)
            st.altair_chart(weekday_chart, use_container_width=True)

        # 날짜별 그래프
        st.subheader("🗓️ 날짜별 수면 시간")
        chart = alt.Chart(df_valid).mark_bar().encode(
            x=alt.X("date_for_chart", title="날짜", sort=None),  # 새로 만든 컬럼 사용
            y=alt.Y("sleep_minutes", title="수면 시간 (분)", scale=alt.Scale(domain=[0, 720])),
            tooltip=["sleep_start", "sleep_end", "sleep_time_str"]
        ).properties(width=700, height=400)
        st.altair_chart(chart, use_container_width=True)


    else:
        st.info("유효한 수면 기록이 없습니다.")
else:
    st.info("아직 수면 기록이 없습니다.")

# -- 다음 날짜로 이동 버튼 --
if st.button("➡️ 다음 날짜로 이동"):
    st.session_state.current_date += timedelta(days=1)
    save_current_date_to_file(st.session_state.current_date)

    st.sidebar.subheader("➡️ 다음 날짜 이동 후 (세션 상태)")
    st.sidebar.write(f"새로운 current_date: {st.session_state.current_date.strftime('%Y-%m-%d')}")
    st.rerun()  # 앱 새로고침

st.markdown("---")

# -- 기록 초기화 --
st.subheader("🧹 기록 초기화")

if st.button("🗑️ 모든 기록 삭제 및 날짜 초기화"):
    if os.path.exists(FILE):
        os.remove(FILE)
    df_init = pd.DataFrame(columns=["date", "sleep_start", "sleep_end"])
    df_init.to_csv(FILE, index=False)

    st.session_state.current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    save_current_date_to_file(st.session_state.current_date)
    st.success("모든 기록이 삭제되고 날짜가 초기화되었습니다.")
    st.rerun()
