import streamlit as st
import folium
from streamlit_folium import st_folium

# 페이지 기본 설정
st.set_page_config(page_title="나만의 여행 플래너", layout="wide")

# 1. 데이터 초기화 (세션 상태를 사용하여 데이터 유지)
if 'itinerary' not in st.session_state:
    # 1일차부터 13일차까지 빈 리스트 생성
    st.session_state.itinerary = {f"{i}일차": [] for i in range(1, 14)}
    
    # [예시 데이터] 1일차에 파리 예시 넣어두기 (사용자가 보고 이해하기 쉽도록)
    st.session_state.itinerary["1일차"] = [
        {"name": "에펠탑", "lat": 48.8584, "lon": 2.2945},
        {"name": "루브르 박물관", "lat": 48.8606, "lon": 2.3376},
        {"name": "몽마르뜨 언덕", "lat": 48.8867, "lon": 2.3431}
    ]

# 2. 사이드바: 날짜 선택 및 장소 추가
st.sidebar.title("📅 여행 일정 선택")
selected_day = st.sidebar.radio("날짜를 선택하세요:", list(st.session_state.itinerary.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader(f"📍 {selected_day} 장소 추가하기")

# 장소 입력 폼
with st.sidebar.form(key='add_location_form'):
    loc_name = st.text_input("장소 이름 (예: 숙소, 식당)")
    col1, col2 = st.columns(2)
    # 구글맵에서 우클릭하면 위도/경도를 알 수 있음을 안내
    lat = col1.number_input("위도 (Latitude)", format="%.4f", value=0.0)
    lon = col2.number_input("경도 (Longitude)", format="%.4f", value=0.0)
    submit_button = st.form_submit_button(label='장소 추가')

    if submit_button:
        if loc_name and lat != 0.0 and lon != 0.0:
            st.session_state.itinerary[selected_day].append({
                "name": loc_name,
                "lat": lat,
                "lon": lon
            })
            st.success(f"{loc_name} 추가 완료!")
        else:
            st.error("이름과 좌표를 모두 입력해주세요.")

# 장소 초기화 버튼
if st.sidebar.button(f"{selected_day} 일정 초기화"):
    st.session_state.itinerary[selected_day] = []
    st.rerun()

# 3. 메인 화면: 지도 및 경로 표시
st.title(f"🗺️ {selected_day} 여행 경로")

# 해당 날짜의 방문지 리스트 가져오기
locations = st.session_state.itinerary[selected_day]

if not locations:
    st.info("아직 등록된 장소가 없습니다. 사이드바에서 장소를 추가해주세요.")
    # 기본 지도는 서울로 설정 (또는 원하는 도시)
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
    st_folium(m, width="100%", height=600)

else:
    # 지도의 중심을 첫 번째 장소로 설정
    start_lat = locations[0]['lat']
    start_lon = locations[0]['lon']
    m = folium.Map(location=[start_lat, start_lon], zoom_start=13)

    # 마커 및 경로 좌표 수집
    route_coords = []
    
    for i, loc in enumerate(locations):
        # 마커 추가
        folium.Marker(
            [loc['lat'], loc['lon']],
            popup=loc['name'],
            tooltip=f"{i+1}. {loc['name']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
        
        route_coords.append([loc['lat'], loc['lon']])

    # 경로(선) 그리기 및 클릭 이벤트(팝업) 추가
    for i in range(len(route_coords) - 1):
        start = route_coords[i]
        end = route_coords[i+1]
        
        # 구글맵 대중교통 길찾기 URL 생성
        # format: https://www.google.com/maps/dir/start_lat,start_lon/end_lat,end_lon/data=!3e3 (3e3=transit)
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={start[0]},{start[1]}&destination={end[0]},{end[1]}&travelmode=transit"
        
        # HTML 링크를 팝업에 삽입
        popup_html = f"""
        <div style="width:150px">
            <b>구간 {i+1} -> {i+2}</b><br>
            <a href="{gmaps_url}" target="_blank" style="text-decoration:none; color:white; background-color:#4285F4; padding:5px; border-radius:5px; display:inline-block; margin-top:5px;">
                🚌 구글맵 경로 보기
            </a>
        </div>
        """
        
        folium.PolyLine(
            locations=[start, end],
            color="red",
            weight=5,
            opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

    # 지도 출력
    st_folium(m, width="100%", height=700)

# 하단에 장소 목록 텍스트로 표시
st.markdown("### 📝 방문 예정 목록")
for idx, loc in enumerate(locations):
    st.write(f"{idx+1}. {loc['name']} (위도: {loc['lat']}, 경도: {loc['lon']})")
