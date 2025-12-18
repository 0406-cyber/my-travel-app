import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="영구 저장 여행 플래너", layout="wide")

# 1. 구글 시트 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 시트에서 데이터 읽어오기 (없으면 빈 데이터프레임 생성)
try:
    df = conn.read(ttl=0) # 실시간으로 읽기 위해 캐시 해제
except:
    df = pd.DataFrame(columns=["day", "name", "lat", "lon"])

# 2. 사이드바 설정
st.sidebar.title("📅 일정 관리 (자동 저장)")
days = [f"{i}일차" for i in range(1, 14)]
selected_day = st.sidebar.radio("날짜 선택", days)

st.sidebar.markdown("---")
st.sidebar.subheader("📍 장소 수동 추가")
with st.sidebar.form("add_form", clear_on_submit=True):
    name = st.text_input("장소 이름")
    lat = st.number_input("위도 (Lat)", format="%.6f")
    lon = st.number_input("경도 (Lon)", format="%.6f")
    submit = st.form_submit_button("일정에 추가")

    if submit and name and lat and lon:
        new_data = pd.DataFrame([{"day": selected_day, "name": name, "lat": lat, "lon": lon}])
        df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=df) # 구글 시트에 즉시 업데이트
        st.success("시트에 저장되었습니다!")
        st.rerun()

# 3. 메인 화면: 선택한 날짜의 데이터만 필터링
current_day_df = df[df["day"] == selected_day]

st.title(f"🗺️ {selected_day} 경로")

if not current_day_df.empty:
    locations = current_day_df.to_dict('records')
    
    # 지도 생성 (첫 번째 장소 기준)
    m = folium.Map(location=[locations[0]['lat'], locations[0]['lon']], zoom_start=14)
    
    points = []
    for i, loc in enumerate(locations):
        folium.Marker([loc['lat'], loc['lon']], tooltip=loc['name']).add_to(m)
        points.append([loc['lat'], loc['lon']])
        
    for i in range(len(points)-1):
        p1, p2 = points[i], points[i+1]
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={p1[0]},{p1[1]}&destination={p2[0]},{p2[1]}&travelmode=transit"
        html = f'<b>{locations[i]["name"]} → {locations[i+1]["name"]}</b><br><a href="{g_url}" target="_blank">🚌 대중교통 경로보기</a>'
        folium.PolyLine([p1, p2], color="red", weight=5, popup=folium.Popup(html, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)

    # 삭제 기능
    st.subheader("📋 목록 관리")
    for idx, row in current_day_df.iterrows():
        col1, col2 = st.columns([4, 1])
        col1.write(f"- {row['name']}")
        if col2.button("삭제", key=f"del_{idx}"):
            df = df.drop(idx)
            conn.update(data=df)
            st.rerun()
else:
    st.info("장소를 추가해 주세요. 데이터는 구글 시트에 안전하게 저장됩니다.")
