import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
import os

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

        # 當回到起點 V1，且路徑長度大於 1 時，進行最佳解檢查
        if curr == 'V1' and len(path) > 1:
            # 💡 修正：如果整趟路線一個設施都沒玩到（rides_count == 0），視為無效行程，直接拒絕！
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
                # 🌟 關鍵防呆限制：如果這個設施還沒被玩過（不在 visited_rides 裡面），且它不是起點 V1
                # 那就絕對不能「只路過不玩」，必須強制跳過這個分支（不執行 _dfs）
                if neighbor != 'V1' and (neighbor not in visited_rides):
                    pass  # 沒玩過就不能純路過，直接不建立這個分支
                else:
                    # 只有「已經玩過該設施」或「要回起點 V1」時，才允許純路過
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

        recommended_path = result['path'] 
        
        st.subheader("推薦遊園路線圖")
        
        # 1. 建立圖形結構 (對照表2的聯通關係)
        G = nx.Graph()
        edges = [
            ('V1', 'V2'), ('V1', 'V3'), ('V2', 'V3'), ('V2', 'V4'),
            ('V3', 'V6'), ('V4', 'V5'), ('V4', 'V6'), ('V5', 'V6')
        ]
        G.add_edges_from(edges)
        
        # 2. 固定節點在網頁上的擺放位置 (完美對齊報告圖 image_bdca24.png 的視覺位置)
        # 比例尺與相對位置均依據：V1在最左，V2在中上，V3在右上，V4在中下，V5在右下，V6在最右
        pos = {
            'V1': (0.0,  0.0),   # 入口廣場 (最左邊中心)
            'V2': (1.5,  1.5),   # 雲霄飛車 (中偏上)
            'V3': (3.0,  0.8),   # 摩天輪   (右偏上)
            'V4': (1.5, -1.5),   # 鬼屋     (中偏下)
            'V5': (3.5, -2.0),   # 漂漂河   (右偏下)
            'V6': (5.0, -0.2)    # 旋轉木馬 (最右邊中心)
        }
        
        # 設施名稱對照表 (讓地圖上直接顯示中文名稱而非單純的 V1、V2)
        labels = {
            'V1': '入口廣場\n(V1)',
            'V2': '雲霄飛車\n(V2)',
            'V3': '摩天輪\n(V3)',
            'V4': '鬼屋\n(V4)',
            'V5': '漂漂河\n(V5)',
            'V6': '旋轉木馬\n(V6)'
        }
        
        # 3. 找出推薦路線經過的邊
        path_edges = list(zip(recommended_path, recommended_path[1:]))

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
        
        # 取得字型實體檔案路徑
        font_p = setup_chinese_font()
        if font_p:
            # 🌟 建立一個強制的字型屬性物件
            my_font = fm.FontProperties(fname=font_p)
        else:
            my_font = None
        
        # ==========================================
        # 🗺️ 繪製推薦路線地圖（完整版）
        # ==========================================
        
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # 使用有向圖（才有箭頭）
        G = nx.DiGraph()
        
        # 邊資料（加入權重）
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
        
        # ==========================================
        # 節點位置
        # ==========================================
        
        pos = {
            'V1': (0.0,  0.0),
            'V2': (1.5,  1.5),
            'V3': (3.0,  0.8),
            'V4': (1.5, -1.5),
            'V5': (3.5, -2.0),
            'V6': (5.0, -0.2)
        }
        
        # ==========================================
        # 畫節點
        # ==========================================
        
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color='#F8F8F8',
            node_size=2500,
            edgecolors='gray',
            linewidths=2,
            ax=ax
        )
        
        # ==========================================
        # 畫所有灰色邊
        # ==========================================
        
        nx.draw_networkx_edges(
            G,
            pos,
            edge_color='lightgray',
            width=2,
            arrows=False,
            ax=ax
        )
        
        # ==========================================
        # 顯示邊的權重
        # ==========================================
        
        edge_labels = {}
        
        for u, v, data in G.edges(data=True):
            edge_labels[(u, v)] = f"wt={data['wt']}\nws={data['ws']}"
        
        edge_texts = nx.draw_networkx_edge_labels(
            G,
            pos,
            edge_labels=edge_labels,
            font_size=9,
            rotate=False,
            ax=ax
        )
        
        # 強制提高層級（關鍵）
        for text in edge_texts.values():
            text.set_zorder(10)
        
        # ==========================================
        # 顯示節點資訊
        # ==========================================
        
        for node, (x, y) in pos.items():
        
            info = vertices[node]
        
            node_text = (
                f"{node}\n"
                f"{info['name']}\n\n"
                f"t{info['Wt']}  "
                f"c{info['Wc']}  "
                f"e{info['We']}  "
                f"p{info['Wp']}"
            )
        
            ax.text(
                x,
                y,
                node_text,
                fontproperties=my_font if my_font else None,
                fontsize=10,
                ha='center',
                va='center',
                zorder=3
            )
        
        # ==========================================
        # 推薦路線（紅色箭頭）
        # ==========================================
        
        recommended_path = result['path']
        path_edges = list(zip(recommended_path, recommended_path[1:]))
        
        from matplotlib.patches import FancyArrowPatch

        # ==========================================
        # 畫推薦路線（真正的箭頭）
        # ==========================================
        
        from matplotlib.patches import FancyArrowPatch
        import numpy as np
        
        def offset_vector(x1, y1, x2, y2, offset, base_start, base_end, pos):
            # 永遠用固定順序（例如節點編號小的到大的）來計算垂直向量的方向
            bx1, by1 = pos[base_start]
            bx2, by2 = pos[base_end]
            
            bdx = bx2 - bx1
            bdy = by2 - by1
            length = np.sqrt(bdx*bdx + bdy*bdy)
        
            if length == 0:
                return x1, y1, x2, y2
        
            # 固定基準的垂直單位向量
            nx = -bdy / length
            ny = bdx / length
        
            # 對「當前實際的起終點」進行相同方向的偏移
            return (
                x1 + nx * offset,
                y1 + ny * offset,
                x2 + nx * offset,
                y2 + ny * offset
            )
        
        drawn_pairs = set()
        
        for start, end in path_edges:
            x1, y1 = pos[start]
            x2, y2 = pos[end]
        
            # 排序抓出基準節點（不論去回，base_start 和 base_end 永遠固定）
            base_start, base_end = sorted([start, end])
            pair = (base_start, base_end)
        
            # 判斷方向
            if pair in drawn_pairs:
                # 回程
                offset = -0.05  # 往基準向量的相反方向偏
                color = 'black'
            else:
                # 去程
                offset = 0.05   # 往基準向量的相同方向偏
                color = 'black'
                drawn_pairs.add(pair)
        
            # 傳入 base_start 和 base_end 來固定垂直向量方向
            x1, y1, x2, y2 = offset_vector(x1, y1, x2, y2, offset, base_start, base_end, pos)
        
            arrow = FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle='->',
                mutation_scale=20,
                color=color,
                linewidth=4,
                shrinkA=20,
                shrinkB=20,
                zorder=3
            )
        
            ax.add_patch(arrow)
        
        # ==========================================
        # 美化
        # ==========================================
        
        ax.set_title(
            "主題樂園最佳遊園路線圖",
            fontsize=16,
            fontproperties=my_font if my_font else None
        )
        
        ax.axis('off')
        
        st.pyplot(fig)
                
        
    else:
        st.error("抱歉！在您指定的極限條件下，找不到任何一條可以回到入口的可行路線。請試著放寬限制（例如增加時間或預算）。")
else:
    st.info("請在左側調整您的偏好與資源限制，然後點擊「開始計算最佳路線」。")
