import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests

# ==========================================
# [설정] 배포된 Apps Script URL 입력
# ==========================================
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxX9l9ZZz02wPkwFAFncfP6MunnepVr8W3tFy5PXYsOeqi8zEcdFULsVnaKZWzrA2hPQQ/exec"

st.set_page_config(page_title="자동 저장 여행 플래너", layout="wide")

# 1. 초기 데이터 로드 (앱 켤 때 한 번만 실행)
if 'itinerary' not in st.session_state:
    try:
        response = requests.get(APPS_SCRIPT_URL)
        data = response.json()
        st.session_state.itinerary = pd.DataFrame(data) if data else pd.DataFrame(columns=["day", "name", "lat", "lon"])
    except:
        st.session_state.itinerary = pd.DataFrame(columns=["day", "name", "lat", "lon"])

# 2. 자동 저장 함수 (핵심)
def auto_save():
    """현재 세션의 데이터를 구글 시트에 덮어씌웁니다."""
    try:
        # 전체 데이터를 JSON으로 변환
        all_data = st.session_state.itinerary.to_dict('records')
        payload = {"data": all_data}
        
        # 구글 시트로 전송 (백그라운드 처리 느낌)
        requests.post(APPS_SCRIPT_URL, json=payload)
        
        # 화면 오른쪽 위에 살짝 알림
        st.toast('✅ 자동 저장 완료!', icon='☁️')
    except Exception as e:
        st.toast(f'❌ 저장 실패: {e}', icon='⚠️')

# ==========================================
# [사이드바]
# ==========================================
st.sidebar.title("📅 자동 저장 플래너")
days = [f"{i}일차" for i in range(1, 14)]
selected_day = st.sidebar.radio("날짜 선택", days)

st.sidebar.markdown("---")
with st.sidebar.form("add_form", clear_on_submit=True):
    name = st.text_input("장소 이름")
    lat = st.number_input("위도", format="%.6f")
    lon = st.number_input("경도", format="%.6f")
    
    # [추가] 버튼 누르면 -> 데이터 추가 -> 바로 자동 저장
    if st.form_submit_button("추가하기"):
        if name and lat != 0:
            new_row = {"day": selected_day, "name": name, "lat": lat, "lon": lon}
            st.session_state.itinerary = pd.concat([st.session_state.itinerary, pd.DataFrame([new_row])], ignore_index=True)
            auto_save() # 자동 저장 실행
            st.rerun()

# ==========================================
# [메인 화면]
# ==========================================
st.title(f"🗺️ {selected_day} 경로")

df = st.session_state.itinerary
day_df = df[df["day"] == selected_day].reset_index(drop=True)

# 지도 표시
if not day_df.empty:
    locs = day_df.to_dict('records')
    m = folium.Map(location=[locs[0]['lat'], locs[0]['lon']], zoom_start=13)
    
    points = []
    for i, loc in enumerate(locs):
        folium.Marker([loc['lat'], loc['lon']], tooltip=f"{i+1}. {loc['name']}").add_to(m)
        points.append([loc['lat'], loc['lon']])
    
    for i in range(len(points)-1):
        p1, p2 = points[i], points[i+1]
        g_url = f"https://www.google.com/maps/dir/?api=1&origin={p1[0]},{p1[1]}&destination={p2[0]},{p2[1]}&travelmode=transit"
        folium.PolyLine([p1, p2], color="red", weight=4, popup=folium.Popup(f'<a href="{g_url}" target="_blank">길찾기</a>', max_width=100)).add_to(m)
    
    st_folium(m, width="100%", height=500)

# 순서 변경 및 삭제 (행동 즉시 자동 저장)
st.subheader("📋 순서 관리")

if not day_df.empty:
    for i, row in day_df.iterrows():
        c1, c2, c3, c4 = st.columns([6, 1, 1, 1])
        c1.write(f"**{i+1}. {row['name']}**")
        
        # 원본 데이터 인덱스 찾기
        original_idx = df[(df['day'] == row['day']) & (df['name'] == row['name']) & (df['lat'] == row['lat'])].index[0]

        # [위로] 버튼
        if i > 0 and c2.button("⬆️", key=f"up_{i}"):
            prev_idx = df[(df['day'] == row['day'])].index[i-1]
            # 순서 교체 (Swap)
            df.iloc[original_idx], df.iloc[prev_idx] = df.iloc[prev_idx].copy(), df.iloc[original_idx].copy()
            st.session_state.itinerary = df
            auto_save() # 자동 저장
            st.rerun()
            
        # [아래로] 버튼
        if i < len(day_df) - 1 and c3.button("⬇️", key=f"down_{i}"):
            next_idx = df[(df['day'] == row['day'])].index[i+1]
            df.iloc[original_idx], df.iloc[next_idx] = df.iloc[next_idx].copy(), df.iloc[original_idx].copy()
            st.session_state.itinerary = df
            auto_save() # 자동 저장
            st.rerun()
            
        # [삭제] 버튼
        if c4.button("🗑️", key=f"del_{i}"):
            st.session_state.itinerary = df.drop(original_idx).reset_index(drop=True)
            auto_save() # 자동 저장
            st.rerun()

else:
    st.info("장소를 추가하면 자동으로 저장됩니다.")
