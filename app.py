import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="영구 저장 여행 플래너", layout="wide")

# 1. 구글 시트 연결
# Secrets의 [connections.gsheets] 설정을 사용합니다.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hS58vMJdftz_9Boc-TSag9QxUt2q78TNVjpSHKfln00/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 데이터 읽기
    df = conn.read(ttl=0)
except Exception as e:
    st.error(f"⚠️ 연결 실패: {e}")
    df = pd.DataFrame(columns=["day", "name", "lat", "lon"])

# 2. 사이드바 입력
st.sidebar.title("📅 일정 관리")
selected_day = st.sidebar.radio("날짜 선택", [f"{i}일차" for i in range(1, 14)])

with st.sidebar.form("add_form", clear_on_submit=True):
    name = st.text_input("장소 이름")
    lat = st.number_input("위도 (Lat)", format="%.6f")
    lon = st.number_input("경도 (Lon)", format="%.6f")
    if st.form_submit_button("일정에 추가"):
        if name and lat != 0:
            new_row = pd.DataFrame([{"day": selected_day, "name": name, "lat": lat, "lon": lon}])
            df = pd.concat([df, new_row], ignore_index=True)
            # 주소를 명시적으로 전달하여 업데이트
            conn.update(spreadsheet=SHEET_URL, data=df)
            st.success("저장 완료!")
            st.rerun()

# 3. 지도 표시
day_df = df[df["day"] == selected_day]
st.title(f"🗺️ {selected_day} 경로")

if not day_df.empty:
    locs = day_df.to_dict('records')
    m = folium.Map(location=[locs[0]['lat'], locs[0]['lon']], zoom_start=14)
    points = [[l['lat'], l['lon']] for l in locs]
    
    for i, loc in enumerate(locs):
        folium.Marker(points[i], tooltip=loc['name']).add_to(m)
        
    for i in range(len(points)-1):
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={points[i][0]},{points[i][1]}&destination={points[i+1][0]},{points[i+1][1]}&travelmode=transit"
        html = f'<a href="{g_url}" target="_blank">🚌 대중교통 경로보기</a>'
        folium.PolyLine([points[i], points[i+1]], color="red", weight=5, popup=folium.Popup(html, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)
    
    # 삭제 기능
    for idx, row in day_df.iterrows():
        col1, col2 = st.columns([4, 1])
        col1.write(f"- {row['name']}")
        if col2.button("삭제", key=f"del_{idx}"):
            df = df.drop(idx)
            conn.update(spreadsheet=SHEET_URL, data=df)
            st.rerun()
else:
    st.info("장소를 추가해 주세요.")
