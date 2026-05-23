import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
import os
import time  # 引入時間模組來控制網頁更新頻率

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
    'V4': [('V2', 10, 3), ('V5', 5, 2), ('V6', 7, 1)],
    'V5': [('V4', 5, 2), ('V6', 12, 4)],
    'V6': [('V3', 8, 5), ('V4', 7, 1), ('V5', 12, 4)]
}

# ==========================================
# 2. 核心搜尋演算法 (加入網頁動態監控)
# ==========================================
class ParkPlanner:
    def __init__(self, vertices, graph, status_placeholder=None, log_placeholder=None):
        self.vertices = vertices
        self.graph = graph
        self.best_solution = None
        self.best_metrics = [-1, -1, float('-inf'), float('-inf'), float('-inf')]
        
        # Streamlit 顯示元件
        self.status_placeholder = status_placeholder
        self.log_placeholder = log_placeholder
        self.total_states_explored = 0
        self.prune_count = 0
        self.last_update_time = time.time()
        self.recent_logs = []

    def solve(self, max_time, max_cost, max_energy, max_sun):
        self.best_solution = None
        self.best_metrics = [-1, -1, float('-inf'), float('-inf'), float('-inf')]
        self.total_states_explored = 0
        self.prune_count = 0
        self.recent_logs = ["🚀 開始進行深度優先搜尋 (DFS)..."]
        
        self._dfs('V1', 0, 0, 0, 0, ['V1'], set(), 0, max_time, max_cost, max_energy, max_sun)
        
        # 搜尋結束後更新最後狀態
        if self.status_placeholder:
            self.status_placeholder.markdown(
                f"📊 **搜尋結束統計**：總共探索了 `{self.total_states_explored}` 個狀態，"
                f"成功剪枝 `{self.prune_count}` 次。"
            )
        return self.best_solution

    def _update_ui(self, current_path, message, is_pruned=False):
        """輔助函式：用來控制 Streamlit 介面的動態重新渲染"""
        self.total_states_explored += 1
        if is_pruned:
            self.prune_count += 1
            
        # 限制每 0.05 秒才更新一次網頁，避免 Streamlit 頻繁重繪導致網頁凍結
        current_time = time.time()
        if current_time - self.last_update_time > 0.05:
            path_str = " ➔ ".join(current_path)
            
            # 更新狀態列
            if self.status_placeholder:
                self.status_placeholder.markdown(
                    f"🔄 **當前搜尋狀態**：已探索 `{self.total_states_explored}` 個節點 | "
                    f"已剪枝次數：`{self.prune_count}` 次\n\n"
                    f"📍 **當前嘗試路徑**：`{path_str}`"
                )
            
            # 更新即時日誌紀錄 (只保留最近 5 條)
            if self.log_placeholder:
                log_style = "🔴 [剪枝] " if is_pruned else "🟢 [探索] "
                self.recent_logs.append(f"{log_style}路徑: {path_str} ({message})")
                if len(self.recent_logs) > 5:
                    self.recent_logs.pop(0)
                
                # 組合文字輸出
                log_text = "\n".join([f"- {log}" for log in self.recent_logs])
                self.log_placeholder.markdown(log_text)
                
            self.last_update_time = current_time

    def _dfs(self, curr, t, c, e, s, path, visited_rides, pref, max_t, max_c, max_e, max_s):
        # 條件 1：超出資源限制 -> 剪枝
        if t > max_t or c > max_c or e > max_e or s > max_s:
            reason = []
            if t > max_t: reason.append(f"時間超限({t}>{max_t})")
            if c > max_c: reason.append(f"預算超限({c}>{max_c})")
            if e > max_e: reason.append(f"體力超限({e}>{max_e})")
            if s > max_s: reason.append(f"曝曬超限({s}>{max_s})")
            self._update_ui(path, ", ".join(reason), is_pruned=True)
            return
            
        # 條件 2：剩餘能玩的設施加起來也無法超越目前最佳解 -> 剪枝
        remaining_rides = len(self.vertices) - 1 - len(visited_rides)
        if len(visited_rides) + remaining_rides < self.best_metrics[0]:
            self._update_ui(path, "潛在遊玩數量無法超越當前最佳解", is_pruned=True)
            return

        # 動態通知目前探索點
        self._update_ui(path, f"抵達 {self.vertices[curr]['name']}")

        # 當回到起點 V1，且路徑長度大於 1 時，進行最佳解檢查
        if curr == 'V1' and len(path) > 1:
            if len(visited_rides) == 0:
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

            # 分支二：選擇「只經過、不遊玩」（或回到起點 V1）
            if path.count(neighbor) < 2:
                if neighbor != 'V1' and (neighbor not in visited_rides):
                    pass  # 沒玩過就不能純路過，直接不建立這個分支
                else:
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
    
    st.subheader("🕵️ 演算法即時計算過程")
    # 建立兩個 Streamlit 的空容器，用來動態刷新內容
    status_box = st.empty()
    
    # 用 st.expander 把詳細的動態日誌收納起來，介面比較整潔
    with st.expander("查看即時搜尋日誌與剪枝動作", expanded=True):
        log_box = st.empty()
        
    # 初始化 Planner 並帶入 UI 容器
    planner = ParkPlanner(vertices, graph, status_placeholder=status_box, log_placeholder=log_box)
    
    # 執行 solve (執行期間網頁會動態刷新)
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

        recommended_path = result['path'] 
        
        st.subheader("推薦遊園路線圖")
        
        # 1. 建立圖形結構
        G = nx.Graph()
        edges = [
            ('V1', 'V2'), ('V1', 'V3'), ('V2', 'V3'), ('V2', 'V4'),
            ('V3', 'V6'), ('V4', 'V5'), ('V4', 'V6'), ('V5', 'V6')
        ]
        G.add_edges_from(edges)
        
        pos = {
            'V1': (0.0,  0.0),  
            'V2': (1.5,  1.5),  
            'V3': (3.0,  0.8),  
            'V4': (1.5, -1.5),  
            'V5': (3.5, -2.0),  
            'V6': (5.0, -0.2)   
        }
        
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
        
        font_p = setup_chinese_font()
        my_font = fm.FontProperties(fname=font_p) if font_p else None
        
        # 🗺️ 繪製推薦路線地圖
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
        
        nx.draw_networkx_nodes(G, pos, node_color='#F8F8F8', node_size=2500, edgecolors='gray', linewidths=2, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='lightgray', width=2, arrows=False, ax=ax)
        
        edge_labels = {(u, v): f"wt={data['wt']}\nws={data['ws']}" for u, v, data in G.edges(data=True)}
        edge_texts = nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, rotate=False, ax=ax)
        for text in edge_texts.values():
            text.set_zorder(10)
        
        for node, (x, y) in pos.items():
            info = vertices[node]
            node_text = f"{node}\n{info['name']}\n\nt{info['Wt']}  c{info['Wc']}  e{info['We']}  p{info['Wp']}"
            ax.text(x, y, node_text, fontproperties=my_font, fontsize=10, ha='center', va='center', zorder=3)
        
        from matplotlib.patches import FancyArrowPatch
        import numpy as np
        
        def offset_vector(x1, y1, x2, y2, offset, base_start, base_end, pos):
            bx1, by1 = pos[base_start]
            bx2, by2 = pos[base_end]
            bdx, bdy = bx2 - bx1, by2 - by1
            length = np.sqrt(bdx*bdx + bdy*bdy)
            if length == 0: return x1, y1, x2, y2
            nx_val = -bdy / length
            ny_val = bdx / length
            return (x1 + nx_val * offset, y1 + ny_val * offset, x2 + nx_val * offset, y2 + ny_val * offset)
        
        drawn_pairs = set()
        for start, end in path_edges:
            x1, y1 = pos[start]
            x2, y2 = pos[end]
            base_start, base_end = sorted([start, end])
            pair = (base_start, base_end)
            
            offset = -0.05 if pair in drawn_pairs else 0.05
            drawn_pairs.add(pair)
            
            x1, y1, x2, y2 = offset_vector(x1, y1, x2, y2, offset, base_start, base_end, pos)
            arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='->', mutation_scale=20, color='red', linewidth=4, shrinkA=20, shrinkB=20, zorder=3)
            ax.add_patch(arrow)
        
        ax.set_title("主題樂園最佳遊園路線圖", fontsize=16, fontproperties=my_font)
        ax.axis('off')
        st.pyplot(fig)
        
    else:
        st.error("抱歉！在您指定的極限條件下，找不到任何一條可以回到入口的可行路線。請試著放寬限制（例如增加時間或預算）。")
else:
    st.info("請在左側調整您的偏好與資源限制，然後點擊「開始計算最佳路線」。")
