import streamlit as st
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(page_title="스마트 여행 플래너", layout="wide")

# 데이터 저장 구조
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = {f"{i}일차": [] for i in range(1, 14)}

# 구글맵 링크에서 좌표를 추출하는 함수
def extract_coords(url):
    # 구글맵 공유 링크에서 위도/경도 패턴 찾기
    regex = r"@(-?\[0-9.\]+),(-?\[0-9.\]+)"
    match = re.search(regex, url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

st.sidebar.title("📅 일정 관리")
selected_day = st.sidebar.radio("날짜 선택", list(st.session_state.itinerary.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("📍 장소 추가 (구글맵 이용)")

# 장소 이름과 구글맵 링크 입력
loc_name = st.sidebar.text_input("1. 장소 이름 (예: 숙소, 맛집)")
gmaps_link = st.sidebar.text_input("2. 구글맵 링크 붙여넣기")
st.sidebar.caption("구글맵에서 '공유' -> '링크 복사' 후 붙여넣으세요.")

if st.sidebar.button("장소 추가"):
    if loc_name and gmaps_link:
        # 링크에서 좌표 추출 시도 (직접 URL에 좌표가 있는 경우)
        lat, lon = extract_coords(gmaps_link)
        
        # 만약 짧은 링크(goo.gl)라서 좌표가 안 보인다면? 
        # 이 부분은 서버에서 실제 페이지를 열어봐야 하므로 
        # 사용자에게 위경도를 직접 넣는 칸도 예비로 둡니다.
        if lat and lon:
            st.session_state.itinerary[selected_day].append({"name": loc_name, "lat": lat, "lon": lon})
            st.success("추가되었습니다!")
        else:
            st.error("링크에서 위치를 찾을 수 없습니다. 좌표를 직접 입력하거나 다른 링크를 써주세요.")
    else:
        st.warning("이름과 링크를 모두 입력해주세요.")

# 지도 표시 로직 (기존과 동일하되 선 클릭 시 구글맵 연결 유지)
st.title(f"🗺️ {selected_day} 경로")
locations = st.session_state.itinerary[selected_day]

if locations:
    m = folium.Map(location=[locations[0]['lat'], locations[0]['lon']], zoom_start=14)
    route_coords = []
    
    for i, loc in enumerate(locations):
        folium.Marker([loc['lat'], loc['lon']], tooltip=loc['name']).add_to(m)
        route_coords.append([loc['lat'], loc['lon']])
        
    for i in range(len(route_coords)-1):
        start, end = route_coords[i], route_coords[i+1]
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={start[0]},{start[1]}&destination={end[0]},{end[1]}&travelmode=transit"
        popup_html = f'<a href="{g_url}" target="_blank">🚌 대중교통 경로보기</a>'
        folium.PolyLine([start, end], color="red", weight=4, popup=folium.Popup(popup_html, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)
else:
    st.info("장소를 추가해주세요.")
