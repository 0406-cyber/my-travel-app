import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

st.set_page_config(page_title="나의 여행 플래너", layout="wide")

# 1. 데이터 로드 (시션 상태 이용)
# 구글 시트 연동 에러를 피하기 위해, 세션에 데이터를 담고 
# 원할 때 파일로 저장하거나 불러오는 방식이 가장 안전합니다.
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = pd.DataFrame(columns=["day", "name", "lat", "lon"])

# 2. 사이드바 관리
st.sidebar.title("📅 일정 관리")
days = [f"{i}일차" for i in range(1, 14)]
selected_day = st.sidebar.radio("날짜 선택", days)

st.sidebar.markdown("---")
st.sidebar.subheader("📍 장소 추가")
with st.sidebar.form("add_form", clear_on_submit=True):
    name = st.text_input("장소 이름")
    lat = st.number_input("위도 (Lat)", format="%.6f", help="구글맵에서 복사한 위도")
    lon = st.number_input("경도 (Lon)", format="%.6f", help="구글맵에서 복사한 경도")
    if st.form_submit_button("일정에 추가"):
        if name and lat != 0:
            new_data = pd.DataFrame([{"day": selected_day, "name": name, "lat": lat, "lon": lon}])
            st.session_state.itinerary = pd.concat([st.session_state.itinerary, new_data], ignore_index=True)
            st.rerun()

# 3. 데이터 보존 기능 (구글 시트 대신 사용)
st.sidebar.markdown("---")
st.sidebar.subheader("💾 데이터 보관")
# CSV로 내보내기
csv = st.session_state.itinerary.to_csv(index=False).encode('utf-8-sig')
st.sidebar.download_button("내 일정 다운로드(CSV)", data=csv, file_name="my_travel.csv", mime="text/csv")

# 불러오기
uploaded_file = st.sidebar.file_opener = st.sidebar.file_uploader("저장된 파일 불러오기", type="csv")
if uploaded_file:
    st.session_state.itinerary = pd.read_csv(uploaded_file)
    st.sidebar.success("일정을 불러왔습니다!")

# 4. 메인 화면 지도
st.title(f"🗺️ {selected_day} 경로")
df = st.session_state.itinerary
day_df = df[df["day"] == selected_day]

if not day_df.empty:
    locs = day_df.to_dict('records')
    m = folium.Map(location=[locs[0]['lat'], locs[0]['lon']], zoom_start=14)
    points = [[l['lat'], l['lon']] for l in locs]
    
    for i, loc in enumerate(locs):
        folium.Marker(points[i], tooltip=f"{i+1}. {loc['name']}").add_to(m)
        
    for i in range(len(points)-1):
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={points[i][0]},{points[i][1]}&destination={points[i+1][0]},{points[i+1][1]}&travelmode=transit"
        html = f'<div style="width:150px"><b>{i+1}번→{i+2}번</b><br><a href="{g_url}" target="_blank" style="color:blue;text-decoration:none;">🚌 길찾기 연결</a></div>'
        folium.PolyLine([points[i], points[i+1]], color="red", weight=5, popup=folium.Popup(html, max_width=200)).add_to(m)
    
    st_folium(m, width="100%", height=500)
    
    # 목록 삭제
    st.subheader("📋 장소 목록 (누르면 삭제)")
    for idx, row in day_df.iterrows():
        col1, col2 = st.columns([5, 1])
        col1.write(f"{row['name']}")
        if col2.button("삭제", key=f"del_{idx}"):
            st.session_state.itinerary = st.session_state.itinerary.drop(idx)
            st.rerun()
else:
    st.info("왼쪽에서 장소를 추가하세요. 여행 중 데이터가 사라지지 않게 하려면 '다운로드' 버튼을 눌러 보관하세요!")
