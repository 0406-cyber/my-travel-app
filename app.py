import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests

# ==========================================
# [설정] 여기에 Apps Script 배포 URL을 넣으세요
# ==========================================
APPS_SCRIPT_URL = "https://script.google.com/macros/s/여기에_복사한_주소를_붙여넣으세요/exec"

st.set_page_config(page_title="여행 플래너 (순서변경 가능)", layout="wide")

# 1. 세션 상태 초기화 (데이터를 앱 켜져있는 동안 관리)
if 'itinerary' not in st.session_state:
    # 초기 데이터 구조
    st.session_state.itinerary = pd.DataFrame(columns=["day", "name", "lat", "lon"])

# 2. 데이터 불러오기 함수 (구글 시트 -> 앱)
def load_from_sheet():
    try:
        response = requests.get(APPS_SCRIPT_URL)
        if response.status_code == 200:
            data = response.json()
            if data:
                st.session_state.itinerary = pd.DataFrame(data)
                st.success("구글 시트에서 데이터를 불러왔습니다!")
            else:
                st.warning("시트가 비어있습니다.")
        else:
            st.error("서버 연결 실패")
    except Exception as e:
        st.error(f"불러오기 에러: {e}")

# 3. 데이터 저장하기 함수 (앱 -> 구글 시트)
def save_to_sheet(row_data):
    try:
        # 데이터 포맷을 {"data": {...}} 형태로 맞춤
        payload = {"data": row_data}
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            st.success("저장 성공!")
        else:
            st.error("저장 실패 (서버 응답 오류)")
    except Exception as e:
        st.error(f"저장 에러: {e}")

# ==========================================
# [사이드바] 설정 및 입력
# ==========================================
st.sidebar.title("📅 일정 관리")

# 데이터 동기화 버튼
col_s1, col_s2 = st.sidebar.columns(2)
if col_s1.button("📂 시트에서 불러오기"):
    load_from_sheet()
    st.rerun()

days = [f"{i}일차" for i in range(1, 14)]
selected_day = st.sidebar.radio("날짜 선택", days)

st.sidebar.markdown("---")
st.sidebar.subheader("📍 장소 추가")
with st.sidebar.form("add_form", clear_on_submit=True):
    name = st.text_input("장소 이름 (예: 숙소, 식당)")
    lat = st.number_input("위도 (Latitude)", format="%.6f")
    lon = st.number_input("경도 (Longitude)", format="%.6f")
    
    if st.form_submit_button("리스트에 추가"):
        if name and lat != 0:
            # 세션에 먼저 추가 (저장은 나중에)
            new_row = {"day": selected_day, "name": name, "lat": lat, "lon": lon}
            st.session_state.itinerary = pd.concat([st.session_state.itinerary, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()

# ==========================================
# [메인 화면]
# ==========================================
st.title(f"🗺️ {selected_day} 경로 및 순서 관리")

# 현재 날짜의 데이터만 필터링
df = st.session_state.itinerary
day_df = df[df["day"] == selected_day].reset_index(drop=True)

# 1. 지도 표시
if not day_df.empty:
    locs = day_df.to_dict('records')
    # 지도 중심: 첫 번째 장소
    m = folium.Map(location=[locs[0]['lat'], locs[0]['lon']], zoom_start=13)
    
    points = []
    for i, loc in enumerate(locs):
        # 마커 추가
        folium.Marker(
            [loc['lat'], loc['lon']],
            popup=loc['name'],
            tooltip=f"{i+1}. {loc['name']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        points.append([loc['lat'], loc['lon']])
    
    # 경로 선 그리기
    for i in range(len(points)-1):
        p1, p2 = points[i], points[i+1]
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={p1[0]},{p1[1]}&destination={p2[0]},{p2[1]}&travelmode=transit"
        html = f'<a href="{g_url}" target="_blank">🚌 길찾기</a>'
        folium.PolyLine([p1, p2], color="red", weight=4, popup=folium.Popup(html, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)
else:
    st.info("장소를 추가하면 지도가 나타납니다.")

# 2. 순서 변경 및 리스트 관리 (여기가 핵심!)
st.subheader("📋 방문 순서 (위아래 버튼으로 이동)")

if not day_df.empty:
    for i, row in day_df.iterrows():
        # 레이아웃: 이름 | 위로 | 아래로 | 저장버튼 | 삭제
        c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 2, 1])
        
        with c1:
            st.write(f"**{i+1}. {row['name']}**")
        
        # 실제 전체 데이터프레임에서의 인덱스 찾기
        original_idx = df[(df['day'] == row['day']) & (df['name'] == row['name']) & (df['lat'] == row['lat'])].index[0]
        
        with c2:
            # 위로 이동 (첫 번째가 아닐 때만)
            if i > 0:
                if st.button("⬆️", key=f"up_{i}"):
                    # 현재 행과 윗 행의 순서를 바꿈 (swap)
                    prev_idx = df[(df['day'] == row['day'])].index[i-1]
                    
                    # Swap Logic
                    df.iloc[original_idx], df.iloc[prev_idx] = df.iloc[prev_idx].copy(), df.iloc[original_idx].copy()
                    st.session_state.itinerary = df
                    st.rerun()

        with c3:
            # 아래로 이동 (마지막이 아닐 때만)
            if i < len(day_df) - 1:
                if st.button("⬇️", key=f"down_{i}"):
                    # 현재 행과 아래 행의 순서를 바꿈
                    next_idx = df[(df['day'] == row['day'])].index[i+1]
                    
                    df.iloc[original_idx], df.iloc[next_idx] = df.iloc[next_idx].copy(), df.iloc[original_idx].copy()
                    st.session_state.itinerary = df
                    st.rerun()
        
        with c4:
            # 개별 저장 버튼 (순서 확정 후 누르세요)
            if st.button("☁️ 시트에 저장", key=f"save_{i}"):
                save_to_sheet({"day": row['day'], "name": row['name'], "lat": row['lat'], "lon": row['lon']})

        with c5:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.itinerary = df.drop(original_idx).reset_index(drop=True)
                st.rerun()

else:
    st.caption("리스트가 비어있습니다.")
