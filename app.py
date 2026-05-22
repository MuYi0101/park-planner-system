import streamlit as st

# ==========================================
# 1. 定義地圖資料模型 (Data Model)
# ==========================================
vertices = {
    'V1': {'name': '入口廣場', 'Wt': 0, 'Wc': 0, 'We': 0, 'Wp': 0},
    'V2': {'name': '雲霄飛車', 'Wt': 150, 'Wc': 15, 'We': 8, 'Wp': 9},
    'V3': {'name': '摩天輪',   'Wt': 20,  'Wc': 100, 'We': 2, 'Wp': 6},
    'V4': {'name': '鬼屋',     'Wt': 25,  'Wc': 120, 'We': 6, 'Wp': 8},
    'V5': {'name': '漂漂河',   'Wt': 80,  'Wc': 30,  'We': 4, 'Wp': 7},
    'V6': {'name': '旋轉木馬', 'Wt': 50,  'Wc': 10,  'We': 1, 'Wp': 5}
}

graph = {
    'V1': [('V2', 5, 2), ('V3', 4, 4)],
    'V2': [('V1', 5, 2), ('V3', 6, 1), ('V4', 10, 3)],
    'V3': [('V1', 4, 4), ('V2', 6, 1), ('V6', 8, 5)],
    'V4': [('V2', 10, 3), ('V5', 5, 2), ('V6', 7, 1)],
    'V5': [('V4', 5, 2), ('V6', 12, 4)],
    'V6': [('V3', 8, 5), ('V4', 7, 1), ('V5', 12, 4)]
}

# ==========================================
# 2. 核心搜尋演算法 (你的核心 Code)
# ==========================================
class ParkPlanner:
    def __init__(self, vertices, graph):
        self.vertices = vertices
        self.graph = graph
        self.best_solution = None
        self.best_metrics = [-1, -1, float('-inf'), float('-inf'), float('-inf')]

    def solve(self, max_time, max_cost, max_energy, max_sun):
        self.best_solution = None
        self.best_metrics = [-1, -1, float('-inf'), float('-inf'), float('-inf')]
        self._dfs('V1', 0, 0, 0, 0, ['V1'], set(), 0, max_time, max_cost, max_energy, max_sun)
        return self.best_solution

    def _dfs(self, curr, t, c, e, s, path, visited_rides, pref, max_t, max_c, max_e, max_s):
        if t > max_t or c > max_c or e > max_e or s > max_s:
            return
        
        remaining_rides = len(self.vertices) - 1 - len(visited_rides)
        if len(visited_rides) + remaining_rides < self.best_metrics[0]:
            return

        if curr == 'V1' and len(path) > 1:
            current_metrics = [len(visited_rides), pref, -t, -c, -s]
            if current_metrics > self.best_metrics:
                self.best_metrics = current_metrics
                self.best_solution = {
                    'path': path,
                    'total_time': t,
                    'total_cost': c,
                    'total_energy': e,
                    'total_sun': s,
                    'total_preference': pref,
                    'rides_count': len(visited_rides)
                }
            return

        for neighbor, edge_t, edge_s in self.graph[curr]:
            if neighbor != 'V1' and neighbor not in visited_rides:
                v_info = self.vertices[neighbor]
                new_t = t + edge_t + v_info['Wt']
                new_c = c + v_info['Wc']
                new_e = e + v_info['We']
                new_s = s + edge_s
                new_pref = pref + v_info['Wp']
                
                visited_rides.add(neighbor)
                self._dfs(neighbor, new_t, new_c, new_e, new_s, 
                          path + [neighbor], visited_rides, new_pref, 
                          max_t, max_c, max_e, max_s)
                visited_rides.remove(neighbor)

            if path.count(neighbor) < 2:
                self._dfs(neighbor, t + edge_t, c, e, s + edge_s, 
                          path + [neighbor], visited_rides, pref, 
                          max_t, max_c, max_e, max_s)

# ==========================================
# 3. Streamlit 網頁使用者介面 (UI)
# ==========================================
st.set_page_config(page_title="主題樂園最佳遊園計畫系統", layout="wide")
st.title("演算法概論：主題樂園最佳遊園計畫系統 (第八組)")

# 側邊欄：輸入條件
st.sidebar.header("請輸入您的遊園限制")
max_time = st.sidebar.slider("時間上限 (分鐘)", 0, 600, 350)
max_cost = st.sidebar.slider("預算上限 (新台幣)", 0, 500, 250)
max_energy = st.sidebar.slider("體力上限 (1-20)", 1, 20, 12)
max_sun = st.sidebar.slider("可接受曝曬指數上限", 1, 30, 15)

st.sidebar.markdown("---")
if st.sidebar.button("開始計算最佳路線"):
    planner = ParkPlanner(vertices, graph)
    result = planner.solve(max_time, max_cost, max_energy, max_sun)
    
    if result:
        st.success("成功生成最佳計畫！")
        
        # 顯示路線推薦
        st.subheader("推薦遊園路線")
        route_display = " ➔ ".join([f"**{vertices[node]['name']} ({node})**" for node in result['path']])
        st.info(route_display)
        
        # 顯示數據指標
        st.subheader("行程數據統計")
        col1, col2, col3 = st.columns(3)
        col1.metric("遊玩設施數量", f"{result['rides_count']} 個")
        col2.metric("總偏好分數", f"{result['total_preference']} 分")
        col3.metric("總花費時間", f"{result['total_time']} 分鐘")
        
        col4, col5, col6 = st.columns(3)
        col4.metric("總花費金額", f"{result['total_cost']} 元")
        col5.metric("體力消耗", f"{result['total_energy']} / {max_energy}")
        col6.metric("累積曝曬指數", f"{result['total_sun']} / {max_sun}")
    else:
        st.error("抱歉！在您指定的極限條件下，找不到任何一條可以回到入口的可行路線。請試著放寬限制（例如增加時間或預算）。")
else:
    st.info("請在左側調整您的偏好與資源限制，然後點擊「開始計算最佳路線」。")