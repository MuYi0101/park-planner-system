import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
import os
import pandas as pd
from matplotlib.patches import FancyArrowPatch
import numpy as np

# ==========================================
# 1. 定義地圖資料模型 (Data Model)
# ==========================================
vertices = {
    'V1': {'name': '入口廣場', 'Wt': 0, 'Wc': 0, 'We': 0, 'Wp': 0},
    'V2': {'name': '雲霄飛車', 'Wt': 15, 'Wc': 150, 'We': 8, 'Wp': 9},
    'V3': {'name': '摩天輪',   'Wt': 20,  'Wc': 100, 'We': 2, 'Wp': 6},
    'V4': {'name': '鬼屋',     'Wt': 25,  'Wc': 120, 'We': 6, 'Wp': 8},
    'V5': {'name': '漂漂河',   'Wt': 30,  'Wc': 80,  'We': 4, 'Wp': 7},
    'V6': {'name': '旋轉木馬', 'Wt': 10,  'Wc': 50,  'We': 1, 'Wp': 5}
}

graph = {
    'V1': [('V2', 5, 2), ('V3', 4, 4)],
    'V2': [('V1', 5, 2), ('V3', 6, 1), ('V4', 10, 3)],
    'V3': [('V1', 4, 4), ('V2', 6, 1), ('V6', 8, 5)],
    'V4': [('V2', 10, 3), ('V5', 5, 2), ('V6', 12, 4)],
    'V5': [('V4', 5, 2), ('V6', 7, 1)],
    'V6': [('V3', 8, 5), ('V4', 12, 4), ('V5', 7, 1)]
}

# ==========================================
# 2. 核心搜尋演算法
# ==========================================
class ParkPlanner:
    def __init__(self, vertices, graph):
        self.vertices = vertices
        self.graph = graph
        self.best_solution = None
        self.best_metrics = [-1, -1, float('-inf'), float('-inf'), float('-inf')]
        self.search_history = []  
        self.step_counter = 0     

    def solve(self, max_time, max_cost, max_energy, max_sun):
        self.best_solution = None
        self.best_metrics = [-1, -1, float('-inf'), float('-inf'), float('-inf')]
        self.search_history = []  
        self.step_counter = 0     
        
        self._dfs('V1', 0, 0, 0, 0, ['V1'], set(), 0, max_time, max_cost, max_energy, max_sun)
        return self.best_solution, self.search_history  

    def _dfs(self, curr, t, c, e, s, path, visited_rides, pref, max_t, max_c, max_e, max_s):
        self.step_counter += 1
        
        is_pruned = t > max_t or c > max_c or e > max_e or s > max_s
        remaining_rides = len(self.vertices) - 1 - len(visited_rides)
        if not is_pruned and (len(visited_rides) + remaining_rides < self.best_metrics[0]):
            is_pruned = True
            reason = "最佳解剪枝 (不可能超越目前最高遊玩數)"
        elif is_pruned:
            reason = f"資源超限 (時:{t}/{max_t}, 費:{c}/{max_c}, 體:{e}/{max_e}, 曬:{s}/{max_s})"
        else:
            reason = "繼續搜尋"

        history_entry = {
            '步數': self.step_counter,
            '當前位置': f"{self.vertices[curr]['name']}({curr})",
            '當前路徑': " ➔ ".join(path),
            '遊玩數': len(visited_rides),
            '累積時間': t,
            '累積花費': c,
            '狀態/結果': reason
        }

        if curr == 'V1' and len(path) > 1:
            if len(visited_rides) == 0:
                history_entry['狀態/結果'] = "無效行程 (未遊玩任何設施)"
                self.search_history.append(history_entry)
                return
                
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
                history_entry['狀態/結果'] = "🌟 找到更佳可行解！"
            else:
                history_entry['狀態/結果'] = "完成環路 (未超越目前最佳解)"
            
            self.search_history.append(history_entry)
            return

        self.search_history.append(history_entry)
        
        if is_pruned:
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
                if neighbor != 'V1' and (neighbor not in visited_rides):
                    pass  
                else:
                    self._dfs(neighbor, t + edge_t, c, e, s + edge_s, 
                              path + [neighbor], visited_rides, pref, 
                              max_t, max_c, max_e, max_s)

# ==========================================
# 3. 獨立的地圖繪製功能 (支援未計算與已計算狀態)
# ==========================================
@st.cache_data
def setup_chinese_font():
    font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf"
    font_path = "NotoSansCJKtc-Regular.otf"
    if not os.path.exists(font_path):
        try:
            response = requests.get(font_url)
            with open(font_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            st.error(f"字型下載失敗: {e}")
            return None
    return font_path

def offset_vector(x1, y1, x2, y2, offset, base_start, base_end, pos):
    bx1, by1 = pos[base_start]
    bx2, by2 = pos[base_end]
    bdx, bdy = bx2 - bx1, by2 - by1
    length = np.sqrt(bdx*bdx + bdy*bdy)
    if length == 0: return x1, y1, x2, y2
    nx_vec, ny_vec = -bdy / length, bdx / length
    return x1 + nx_vec * offset, y1 + ny_vec * offset, x2 + nx_vec * offset, y2 + ny_vec * offset

def draw_park_map(result=None):
    font_p = setup_chinese_font()
    my_font = fm.FontProperties(fname=font_p) if font_p else None

    fig, ax = plt.subplots(figsize=(12, 7))
    G = nx.DiGraph()
    
    edges_with_weights = [
        ('V1', 'V2', {'wt': 5,  'ws': 2}),
        ('V1', 'V3', {'wt': 4,  'ws': 4}),
        ('V2', 'V3', {'wt': 6,  'ws': 1}),
        ('V2', 'V4', {'wt': 10, 'ws': 3}),
        ('V3', 'V6', {'wt': 8,  'ws': 5}),
        ('V4', 'V5', {'wt': 5,  'ws': 2}),
        ('V4', 'V6', {'wt': 7,  'ws': 1}),
        ('V5', 'V6', {'wt': 12, 'ws': 4})
    ]
    G.add_edges_from(edges_with_weights)
    
    pos = {
        'V1': (0.0,  0.0), 'V2': (1.5,  1.5), 'V3': (3.0,  0.8),
        'V4': (1.5, -1.5), 'V5': (3.5, -2.0), 'V6': (5.0, -0.2)
    }
    
    # 繪製基礎節點與邊
    nx.draw_networkx_nodes(G, pos, node_color='#F8F8F8', node_size=2500, edgecolors='gray', linewidths=2, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='lightgray', width=2, arrows=False, ax=ax)
    
    edge_labels = {(u, v): f"wt={data['wt']}\nws={data['ws']}" for u, v, data in G.edges(data=True)}
    edge_texts = nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, rotate=False, ax=ax)
    for text in edge_texts.values():
        text.set_zorder(10)
    
    for node, (x, y) in pos.items():
        info = vertices[node]
        node_text = f"{node}\n{info['name']}\n\n" f"t{info['Wt']}  " f"c{info['Wc']}  " f"e{info['We']}  " f"p{info['Wp']}"
        ax.text(x, y, node_text, fontproperties=my_font, fontsize=10, ha='center', va='center', zorder=3)
    
    # 如果有計算結果，疊加推薦路線（紅色箭頭）
    if result and 'path' in result:
        recommended_path = result['path']
        path_edges = list(zip(recommended_path, recommended_path[1:]))
        drawn_pairs = set()
        for start, end in path_edges:
            x1, y1, x2, y2 = pos[start][0], pos[start][1], pos[end][0], pos[end][1]
            base_start, base_end = sorted([start, end])
            pair = (base_start, base_end)
            offset = -0.05 if pair in drawn_pairs else 0.05
            drawn_pairs.add(pair)
            
            x1, y1, x2, y2 = offset_vector(x1, y1, x2, y2, offset, base_start, base_end, pos)
            arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->', mutation_scale=20, color='red', linewidth=4, shrinkA=20, shrinkB=20, zorder=3)
            ax.add_patch(arrow)
        ax.set_title("主題樂園最佳遊園路線圖 (已生成推薦路線)", fontsize=16, fontproperties=my_font)
    else:
        ax.set_title("主題樂園導覽地圖 (未計算基本狀態)", fontsize=16, fontproperties=my_font)

    ax.axis('off')
    st.pyplot(fig)

# ==========================================
# 4. Streamlit 網頁使用者介面 (UI)
# ==========================================
st.set_page_config(page_title="主題樂園最佳遊園計畫系統", layout="wide")
st.title("演算法概論：主題樂園最佳遊園計畫系統 (第八組)")

# 區塊一：遊園限制輸入區（改為可打字輸入的 number_input）
st.subheader("🛠️ 設定您的遊園限制（請輸入數值）")
with st.container():
    col_input1, col_input2, col_input3, col_input4 = st.columns(4)
    
    # 使用 st.number_input 讓使用者可以直接打字
    max_time = col_input1.number_input("時間上限 (分鐘)", min_value=0, max_value=600, value=70, step=1)
    max_cost = col_input2.number_input("預算上限 (新台幣)", min_value=0, max_value=1000, value=300, step=5)
    max_energy = col_input3.number_input("體力上限 (1-30)", min_value=1, max_value=30, value=15, step=1)
    max_sun = col_input4.number_input("可接受曝曬指數上限", min_value=1, max_value=30, value=15, step=1)
    
    # 開始計算按鈕
    start_calculation = st.button("🚀 開始計算最佳路線", use_container_width=True)

st.markdown("---")

# 初始化計算狀態與變數
result = None
history = None
calculated = False

if start_calculation:
    planner = ParkPlanner(vertices, graph)
    result, history = planner.solve(max_time, max_cost, max_energy, max_sun)
    calculated = True

# 🟢 1. 首先顯示地圖 (無論有沒有計算都要顯示)
st.subheader("🗺️ 園區地圖與路線導覽")
if calculated and result:
    draw_park_map(result=result)  # 顯示帶有紅色軌跡的地圖
else:
    draw_park_map(result=None)   # 顯示初始空地圖

# 處理計算後的結果呈現
if calculated:
    if result:
        st.success("成功生成最佳計畫！")
        st.markdown("---")

        # 🟢 2. 顯示推薦路線
        st.subheader("📍 推薦遊園路線")
        route_display = " ➔ ".join([f"**{vertices[node]['name']} ({node})**" for node in result['path']])
        st.info(route_display)
        
        # 🟢 3. 顯示行程數據統計
        st.subheader("📊 行程數據統計")
        col1, col2, col3 = st.columns(3)
        col1.metric("遊玩設施數量", f"{result['rides_count']} 個")
        col2.metric("總偏好分數", f"{result['total_preference']} 分")
        col3.metric("總花費時間", f"{result['total_time']} 分鐘")
        
        col4, col5, col6 = st.columns(3)
        col4.metric("總花費金額", f"{result['total_cost']} 元")
        col5.metric("體力消耗", f"{result['total_energy']} / {max_energy}")
        col6.metric("累積曝曬指數", f"{result['total_sun']} / {max_sun}")

        # 🟢 4. 顯示演算法計算軌跡
        st.markdown("---")
        st.subheader("🧬 深度優先搜尋 (DFS) 演算法計算軌跡")
        
        with st.expander(f"點擊展開 / 摺疊詳細計算步驟 (全域共執行 {len(history)} 步走訪與剪枝)"):
            df_history = pd.DataFrame(history)
            
            def highlight_cells(val):
                if "🌟" in str(val):
                    return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                elif "資源超限" in str(val) or "剪枝" in str(val):
                    return 'background-color: #f8d7da; color: #721c24;'
                return ''
                
            styled_df = df_history.style.map(highlight_cells, subset=['狀態/結果'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
    else:
        st.error("抱歉！在您指定的極限條件下，找不到任何一條可以回到入口的可行路線。請試著放寬限制（例如增加時間或預算）。")
else:
    st.info("💡 調整上方設定並點擊「開始計算最佳路線」按鈕，系統將在此地圖下方即時生成最推薦的客製化遊園行程數據與計算軌跡。")
