import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests
import json

st.set_page_config(page_title="여행 플래너 (Apps Script)", layout="wide")

# 1. Apps Script URL (방금 복사한 웹 앱 URL을 여기에 넣으세요!)
# 따옴표 안에 주소를 꼭 바꿔주세요.
APPS_SCRIPT_URL = "https://script.google.com/macros/s/아이디가_엄청_긴_주소/exec"

# 2. 데이터 불러오기 함수
def load_data():
    try:
        response = requests.get(APPS_SCRIPT_URL)
        data = response.json()
        if not data:
            return pd.DataFrame(columns=["day", "name", "lat", "lon"])
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["day", "name", "lat", "lon"])

# 3. 데이터 저장하기 함수
def save_data_to_sheet(day, name, lat, lon):
    payload = {
        "day": day,
        "name": name,
        "lat": lat,
        "lon": lon
    }
    # 구글 스크립트로 데이터 전송 (POST)
    requests.post(APPS_SCRIPT_URL, json=payload)

# --- 앱 시작 ---
if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

# 데이터 로드
df = load_data()

st.sidebar.title("📅 일정 관리")
days = [f"{i}일차" for i in range(1, 14)]
selected_day = st.sidebar.radio("날짜 선택", days)

st.sidebar.markdown("---")
with st.sidebar.form("add_form", clear_on_submit=True):
    st.write("📍 장소 추가")
    name = st.text_input("이름")
    lat = st.number_input("위도", format="%.6f")
    lon = st.number_input("경도", format="%.6f")
    
    if st.form_submit_button("저장"):
        if name and lat != 0:
            with st.spinner("구글 시트에 저장 중..."):
                save_data_to_sheet(selected_day, name, lat, lon)
            st.success("저장 성공!")
            st.rerun()

# --- 메인 지도 ---
st.title(f"🗺️ {selected_day} 경로")
day_df = df[df["day"] == selected_day]

if not day_df.empty:
    locs = day_df.to_dict('records')
    m = folium.Map(location=[locs[0]['lat'], locs[0]['lon']], zoom_start=14)
    points = [[l['lat'], l['lon']] for l in locs]
    
    for i, loc in enumerate(locs):
        folium.Marker(points[i], tooltip=loc['name']).add_to(m)
        
    for i in range(len(points)-1):
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={points[i][0]},{points[i][1]}&destination={points[i+1][0]},{points[i+1][1]}&travelmode=transit"
        html = f'<a href="{g_url}" target="_blank">🚌 길찾기</a>'
        folium.PolyLine([points[i], points[i+1]], color="red", weight=5, popup=folium.Popup(html, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)
    
    st.subheader("리스트")
    for idx, row in day_df.iterrows():
        st.write(f"- {row['name']}")
else:
    st.info("데이터가 없습니다. 장소를 추가해보세요!")
