# ==========================================
# 4. Streamlit 網頁前端介面實作
# ==========================================
st.set_page_config(layout="wide") # 寬螢幕排版，左邊放輸入、右邊放地圖與數據

st.title("演算法概論：主題樂園最佳遊園計畫系統 (第八組)")

# 建立左側邊欄輸入遊園限制
st.sidebar.header("請輸入您的遊園限制")
max_time = st.sidebar.slider("時間上限 (分鐘)", min_value=10, max_value=600, value=120, step=5)
max_cost = st.sidebar.slider("預算上限 (新台幣)", min_value=0, max_value=1000, value=500, step=10)
max_energy = st.sidebar.slider("體力上限 (1-30)", min_value=1, max_value=30, value=15, step=1)
max_sun = st.sidebar.slider("可接受曝曬指數上限", min_value=1, max_value=50, value=20, step=1)

# 按鈕觸發計算
if st.sidebar.button("開始計算最佳路線"):
    planner = ParkPlanner(vertices, graph)
    result = planner.solve(max_time, max_cost, max_energy, max_sun)

    if result:
        st.success("🎉 成功生成最佳計畫！")
        
        # 顯示推薦路線
        path_names = [f"{vertices[node]['name']} ({node})" for node in result['path']]
        st.subheader("推薦遊園路線")
        st.info(" ➔ ".join(path_names))
        
        # 數據統計呈現
        st.subheader("行程數據統計")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("遊玩設施數量", f"{result['rides_count']} 個")
            st.metric("總花費金額", f"{result['total_cost']} 元")
        with col2:
            st.metric("總偏好分數", f"{result['total_preference']} 分")
            st.metric("體力消耗", f"{result['total_energy']} / {max_energy}")
        with col3:
            st.metric("總花費時間", f"{result['total_time']} 分鐘")
            st.metric("累積曝曬指數", f"{result['total_sun']} / {max_sun}")

        # -------------------------------------------
        # 5. NetworkX 繪製與報告地圖完全同形狀之圖表
        # -------------------------------------------
        st.subheader("🗺️ 推薦遊園路線圖")
        
        G = nx.Graph()
        edges_list = [
            ('V1', 'V2'), ('V1', 'V3'), ('V2', 'V3'), ('V2', 'V4'),
            ('V3', 'V6'), ('V4', 'V5'), ('V4', 'V6'), ('V5', 'V6')
        ]
        G.add_edges_from(edges_list)

        # 完美對齊 image_bdca24.png 的視覺相對座標
        pos = {
            'V1': (0.0,  0.0),   # 入口廣場
            'V2': (1.5,  1.5),   # 雲霄飛車
            'V3': (3.0,  0.8),   # 摩天輪
            'V4': (1.5, -1.5),   # 鬼屋
            'V5': (3.5, -2.0),   # 漂漂河
            'V6': (5.0, -0.2)    # 旋轉木馬
        }

        labels = {
            'V1': '入口廣場\n(V1)', 'V2': '雲霄飛車\n(V2)', 'V3': '摩天輪\n(V3)',
            'V4': '鬼屋\n(V4)', 'V5': '漂漂河\n(V5)', 'V6': '旋轉木馬\n(V6)'
        }

        # 算出推薦路線經過的線條 (Edges)
        recommended_path = result['path']
        path_edges = list(zip(recommended_path, recommended_path[1:]))

        fig, ax = plt.subplots(figsize=(10, 5))
        
        # 畫出底圖（設施圓圈與所有步道）
        nx.draw_networkx_nodes(G, pos, node_color='#F0F2F6', node_size=1800, edgecolors='gray', ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=edges_list, edge_color='#D3D3D3', width=2, ax=ax)
        
        # 畫上完美的繁體中文標籤 (套用我們全域註冊的字型)
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_family=font_family_name, ax=ax)

        # 用紅色粗體線條高亮標記出系統推薦的行走軌跡！
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='#FF4B4B', width=5, ax=ax)

        ax.axis('off')
        st.pyplot(fig)

    else:
        st.error("❌ 抱歉！在您指定的極限條件下，演算法找不到任何一條可以回到入口的可行路線。請試著放寬左側的限制。")
