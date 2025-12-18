import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim # 검색 기능을 위한 라이브러리

st.set_page_config(page_title="스마트 여행 플래너", layout="wide")

# 라이브러리 설치 안내: requirements.txt에 geopy를 추가해야 합니다.
# 1. 데이터 저장 구조
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = {f"{i}일차": [] for i in range(1, 14)}

# 검색 서비스 설정
geolocator = Nominatim(user_agent="my_travel_planner_v1")

st.sidebar.title("📅 일정 관리")
selected_day = st.sidebar.radio("날짜 선택", list(st.session_state.itinerary.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("📍 장소 검색 및 추가")

# 1. 장소 검색창
search_query = st.sidebar.text_input("장소 이름 입력 (예: 도쿄역, 에펠탑)")

if search_query:
    # 검색 실행
    try:
        results = geolocator.geocode(search_query, exactly_one=False, limit=5)
        
        if results:
            # 검색된 결과들을 선택지로 제공
            options = {res.address: (res.latitude, res.longitude) for res in results}
            selected_address = st.sidebar.selectbox("검색 결과 중 선택:", list(options.keys()))
            
            if st.sidebar.button("이 장소를 일정에 추가"):
                lat, lon = options[selected_address]
                # 장소 이름은 사용자가 입력한 짧은 이름으로 저장
                st.session_state.itinerary[selected_day].append({
                    "name": search_query,
                    "address": selected_address,
                    "lat": lat,
                    "lon": lon
                })
                st.sidebar.success(f"'{search_query}' 추가 완료!")
                st.rerun()
        else:
            st.sidebar.warning("검색 결과가 없습니다.")
    except Exception as e:
        st.sidebar.error("검색 중 오류가 발생했습니다. 다시 시도해주세요.")

# 일정 초기화
if st.sidebar.button(f"{selected_day} 일정 초기화"):
    st.session_state.itinerary[selected_day] = []
    st.rerun()

# 2. 메인 화면: 지도 표시
st.title(f"🗺️ {selected_day} 여행 경로")
locations = st.session_state.itinerary[selected_day]

if locations:
    # 지도의 중심을 첫 번째 장소로
    m = folium.Map(location=[locations[0]['lat'], locations[0]['lon']], zoom_start=14)
    route_coords = []
    
    for i, loc in enumerate(locations):
        # 마커 추가
        folium.Marker(
            [loc['lat'], loc['lon']], 
            popup=f"{i+1}. {loc['name']}",
            tooltip=loc['name']
        ).add_to(m)
        route_coords.append([loc['lat'], loc['lon']])
        
    # 선 긋기 및 구글맵 연결
    for i in range(len(route_coords)-1):
        start, end = route_coords[i], route_coords[i+1]
        # 구글맵 대중교통 경로 URL
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={start[0]},{start[1]}&destination={end[0]},{end[1]}&travelmode=transit"
        
        popup_html = f'''
        <div style="text-align:center;">
            <p><b>{locations[i]['name']} → {locations[i+1]['name']}</b></p>
            <a href="{g_url}" target="_blank" style="background-color:#4285F4; color:white; padding:8px; border-radius:5px; text-decoration:none;">🚌 대중교통 경로보기</a>
        </div>
        '''
        
        folium.PolyLine(
            [start, end], 
            color="red", 
            weight=4, 
            opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)
    
    st_folium(m, width="100%", height=600)
else:
    st.info("왼쪽 사이드바에서 장소를 검색해서 추가해 주세요!")

# 목록 표시
if locations:
    with st.expander("방문 리스트 보기"):
        for i, loc in enumerate(locations):
            st.write(f"{i+1}. {loc['name']} ({loc['address']})")
