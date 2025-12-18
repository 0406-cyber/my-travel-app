import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import pandas as pd

st.set_page_config(page_title="완벽 여행 플래너", layout="wide")

# 1. 데이터 저장소
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = {f"{i}일차": [] for i in range(1, 14)}

geolocator = Nominatim(user_agent="my_travel_app_v2")

st.sidebar.title("📅 일정 관리")
selected_day = st.sidebar.radio("날짜 선택", list(st.session_state.itinerary.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("📍 장소 추가 방식 선택")
tab1, tab2 = st.sidebar.tabs(["🔍 자동 검색", "⌨️ 직접 입력"])

with tab1:
    search_query = st.text_input("장소 이름 (예: 도쿄역, 신주쿠역)")
    if st.button("검색하기"):
        try:
            results = geolocator.geocode(search_query, exactly_one=False, limit=5)
            if results:
                st.session_state.temp_results = {res.address: (res.latitude, res.longitude) for res in results}
            else:
                st.error("결과가 없습니다. '직접 입력'을 이용해주세요.")
        except:
            st.error("검색 서비스 일시 오류입니다.")

    if 'temp_results' in st.session_state and st.session_state.temp_results:
        selected_addr = st.selectbox("검색 결과:", list(st.session_state.temp_results.keys()))
        if st.button("이 장소 추가"):
            lat, lon = st.session_state.temp_results[selected_addr]
            st.session_state.itinerary[selected_day].append({"name": search_query, "lat": lat, "lon": lon})
            st.success("추가 완료!")
            st.rerun()

with tab2:
    st.caption("구글맵에서 '좌표'를 복사해서 넣는 것이 가장 정확합니다.")
    custom_name = st.text_input("장소 이름")
    custom_lat = st.number_input("위도 (Lat)", format="%.6f")
    custom_lon = st.number_input("경도 (Lon)", format="%.6f")
    if st.button("수동 추가"):
        if custom_name and custom_lat and custom_lon:
            st.session_state.itinerary[selected_day].append({"name": custom_name, "lat": custom_lat, "lon": custom_lon})
            st.success("추가 완료!")
            st.rerun()

# --- 메인 화면: 지도 및 경로 ---
st.title(f"🗺️ {selected_day} 일정")
locations = st.session_state.itinerary[selected_day]

if locations:
    # 지도 생성
    m = folium.Map(location=[locations[0]['lat'], locations[0]['lon']], zoom_start=14)
    
    points = []
    for i, loc in enumerate(locations):
        folium.Marker([loc['lat'], loc['lon']], tooltip=loc['name'], 
                      icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
        points.append([loc['lat'], loc['lon']])
        
    # 선 그리기 및 대중교통 링크
    for i in range(len(points)-1):
        p1, p2 = points[i], points[i+1]
        # 구글맵 길찾기 링크 (대중교통 모드)
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={p1[0]},{p1[1]}&destination={p2[0]},{p2[1]}&travelmode=transit"
        
        html = f'<b>{locations[i]["name"]} → {locations[i+1]["name"]}</b><br><a href="{g_url}" target="_blank" style="color:blue;">🚌 대중교통 경로보기</a>'
        folium.PolyLine([p1, p2], color="red", weight=5, opacity=0.7, popup=folium.Popup(html, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)
    
    # 순서 변경 및 삭제 기능
    st.subheader("📋 방문 순서")
    for i, loc in enumerate(locations):
        col1, col2 = st.columns([4, 1])
        col1.write(f"{i+1}. {loc['name']}")
        if col2.button("삭제", key=f"del_{i}"):
            st.session_state.itinerary[selected_day].pop(i)
            st.rerun()
else:
    st.info("왼쪽에서 장소를 추가해 주세요.")
