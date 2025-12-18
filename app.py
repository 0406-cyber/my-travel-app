import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="영구 저장 여행 플래너", layout="wide")

# 1. 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 데이터 읽기 (Secrets 설정을 자동으로 참조)
    df = conn.read(ttl=0)
except Exception as e:
    st.error("⚠️ 구글 시트 연결에 실패했습니다. Secrets 설정을 확인해주세요.")
    df = pd.DataFrame(columns=["day", "name", "lat", "lon"])

# 2. 사이드바 일정 입력
st.sidebar.title("📅 여행 일정 관리")
selected_day = st.sidebar.radio("날짜 선택", [f"{i}일차" for i in range(1, 14)])

st.sidebar.markdown("---")
st.sidebar.subheader("📍 장소 수동 추가")
with st.sidebar.form("add_place_form", clear_on_submit=True):
    name = st.text_input("장소 이름 (예: 숙소, 도쿄타워)")
    lat = st.number_input("위도 (Latitude)", format="%.6f", value=0.0)
    lon = st.number_input("경도 (Longitude)", format="%.6f", value=0.0)
    submitted = st.form_submit_button("일정에 추가")

    if submitted:
        if name and lat != 0:
            new_row = pd.DataFrame([{"day": selected_day, "name": name, "lat": lat, "lon": lon}])
            df = pd.concat([df, new_row], ignore_index=True)
            # 시트 업데이트
            conn.update(data=df)
            st.sidebar.success("저장되었습니다!")
            st.rerun()

# 3. 메인 화면 지도 표시
st.title(f"🗺️ {selected_day} 이동 경로")
day_df = df[df["day"] == selected_day]

if not day_df.empty:
    locs = day_df.to_dict('records')
    # 첫 장소 기준으로 지도 중심 설정
    m = folium.Map(location=[locs[0]['lat'], locs[0]['lon']], zoom_start=14)
    
    points = []
    for i, loc in enumerate(locs):
        folium.Marker([loc['lat'], loc['lon']], tooltip=loc['name']).add_to(m)
        points.append([loc['lat'], loc['lon']])
    
    # 경로 선 긋기
    for i in range(len(points)-1):
        p1, p2 = points[i], points[i+1]
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={p1[0]},{p1[1]}&destination={p2[0]},{p2[1]}&travelmode=transit"
        popup_content = f'<a href="{g_url}" target="_blank">🚌 대중교통 경로보기</a>'
        folium.PolyLine([p1, p2], color="red", weight=5, popup=folium.Popup(popup_content, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)
    
    # 목록 및 삭제
    st.subheader("📋 방문 리스트")
    for idx, row in day_df.iterrows():
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{row['name']}**")
        if col2.button("삭제", key=f"del_{idx}"):
            df = df.drop(idx)
            conn.update(data=df)
            st.rerun()
else:
    st.info("왼쪽 사이드바에서 장소를 추가해 주세요!")
