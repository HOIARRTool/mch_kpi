import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

# ตั้งค่าหน้าเพจ
st.set_page_config(page_title="HA Quality Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 🪄 CSS บังคับความกว้าง Sidebar ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 380px !important;
            max-width: 380px !important;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_data_from_gsheet():
    sheet_id = "11yuZC64CxxRTvluF_FpZywwDIN93exAu1IXBamzwKZU"
    gid = "874433633"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    return pd.read_csv(csv_url)


def extract_plot_data(val):
    if pd.isna(val) or str(val).strip() in ['None', '', '-']:
        return None, ""
    val_str = str(val).strip()
    try:
        clean_part = val_str.split('(')[0]
        num_str = re.sub(r'[^\d.]', '', clean_part)
        if num_str:
            return float(num_str), val_str
        return None, val_str
    except:
        return None, val_str


def evaluate_kpi(current_val, target_str):
    target_str = str(target_str).strip()
    try:
        target_num = float(re.sub(r'[^\d.]', '', target_str))
    except:
        return True

    if '<=' in target_str:
        return current_val <= target_num
    elif '<' in target_str:
        return current_val < target_num
    elif '>=' in target_str:
        return current_val >= target_num
    elif '>' in target_str:
        return current_val > target_num
    elif '=' in target_str:
        return current_val == target_num
    else:
        return current_val >= target_num


try:
    with st.spinner('กำลังประมวลผลข้อมูล...'):
        raw_df = load_data_from_gsheet()

        header_idx = raw_df[raw_df.iloc[:, 0] == 'ตัวชี้วัด'].index[0]
        df = raw_df.copy()
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)

        df = df.dropna(subset=['ตัวชี้วัด'])
        df = df[df['ตัวชี้วัด'].notna() & (df['ตัวชี้วัด'].astype(str).str.strip() != '')]

        if 'เป้าหมาย' in df.columns:
            df = df.dropna(subset=['เป้าหมาย'])
            df = df[~df['เป้าหมาย'].astype(str).str.strip().isin(['', 'None', '-', 'nan'])]

        statuses = []
        for idx, row in df.iterrows():
            t_str = row.get('เป้าหมาย', '')
            q1_raw = row.get('ปี 69 (Q1)')
            if pd.isna(q1_raw) or str(q1_raw).strip() in ['', 'None', '-']:
                statuses.append("⏳ ยังไม่มีข้อมูล")
            else:
                q1_val, _ = extract_plot_data(q1_raw)
                if pd.notna(t_str) and str(t_str).strip() != '':
                    if evaluate_kpi(q1_val or 0, t_str):
                        statuses.append("✅ บรรลุเป้าหมาย")
                    else:
                        statuses.append("⚠️ ไม่บรรลุเป้าหมาย")
                else:
                    statuses.append("⏳ ยังไม่มีข้อมูล")
        df['สถานะ Q1'] = statuses

        # ==========================================
    # 📌 แถบด้านซ้าย (Sidebar)
    # ==========================================
    st.sidebar.markdown(
        "<h3 style='text-align: center; color: #2E7D32; line-height: 1.5;'>DASHBOARD: MFU-MCH-KPI</h3>",
        unsafe_allow_html=True)
    st.sidebar.markdown("---")

    st.sidebar.markdown("**🔍 เลือกตัวชี้วัดเพื่อดูผลการดำเนินการและการวิเคราะห์**")
    default_index = 0
    selected_kpi = st.sidebar.selectbox("คลิกเลือกที่นี่:", df['ตัวชี้วัด'].unique(), index=default_index)
    kpi_data = df[df['ตัวชี้วัด'] == selected_kpi].iloc[0]

    # ==========================================
    # 📌 พื้นที่หลัก (Main Content)
    # ==========================================
    col_title, col_logos = st.columns([3, 1])
    with col_title:
        st.markdown("<h3 style='text-align: left; color: #1f77b4; line-height: 1.5;'>โรงพยาบาลศูนย์การแพทย์ มหาวิทยาลัยแม่ฟ้าหลวง</h3>",
        unsafe_allow_html=True)
    with col_logos:
        st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; padding-top: 15px;">
            <img src="https://raw.githubusercontent.com/HOIARRTool/appqtbi/main/messageImage_1763018963411.jpg" style="height: 70px; margin-right: 15px; object-fit: contain;">
            <img src="https://raw.githubusercontent.com/HOIARRTool/appqtbi/main/csm_logo_mfu_3d_colour_15e5a7a50f.png" style="height: 70px; object-fit: contain;">
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    total_indicators = len(df)
    pass_count = len(df[df['สถานะ Q1'] == '✅ บรรลุเป้าหมาย'])
    fail_count = len(df[df['สถานะ Q1'] == '⚠️ ไม่บรรลุเป้าหมาย'])
    no_data_count = len(df[df['สถานะ Q1'] == '⏳ ยังไม่มีข้อมูล'])

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div style='background-color:#E3F2FD;padding:15px;border-radius:10px;text-align:center;border-left: 5px solid #1976D2;'><h5 style='color:#1565C0;margin:0;font-weight:bold;'>📊 ตัวชี้วัดทั้งหมด</h5><h2 style='color:#0D47A1;margin:10px 0 0 0;'>{total_indicators}</h2></div>",
        unsafe_allow_html=True)
    c2.markdown(
        f"<div style='background-color:#E8F5E9;padding:15px;border-radius:10px;text-align:center;border-left: 5px solid #388E3C;'><h5 style='color:#2E7D32;margin:0;font-weight:bold;'>✅ บรรลุเป้าหมาย</h5><h2 style='color:#1B5E20;margin:10px 0 0 0;'>{pass_count}</h2></div>",
        unsafe_allow_html=True)
    c3.markdown(
        f"<div style='background-color:#FFEBEE;padding:15px;border-radius:10px;text-align:center;border-left: 5px solid #D32F2F;'><h5 style='color:#C62828;margin:0;font-weight:bold;'>⚠️ ไม่บรรลุเป้าหมาย</h5><h2 style='color:#B71C1C;margin:10px 0 0 0;'>{fail_count}</h2></div>",
        unsafe_allow_html=True)
    c4.markdown(
        f"<div style='background-color:#F5F5F5;padding:15px;border-radius:10px;text-align:center;border-left: 5px solid #9E9E9E;'><h5 style='color:#616161;margin:0;font-weight:bold;'>⏳ ยังไม่มีข้อมูล (Q1)</h5><h2 style='color:#424242;margin:10px 0 0 0;'>{no_data_count}</h2></div>",
        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📌 แผงควบคุม (Drill-down Table)
    # ==========================================
    with st.expander("🔍 แผงควบคุม: เจาะลึกรายการตัวชี้วัดตามสถานะ (Drill-down)", expanded=True):
        filter_status = st.radio(
            "คลิกเพื่อดูรายชื่อตัวชี้วัดในแต่ละกลุ่ม:",
            ["✅ บรรลุเป้าหมาย", "⚠️ ไม่บรรลุเป้าหมาย", "⏳ ยังไม่มีข้อมูล", "📊 แสดงทั้งหมด"],
            horizontal=True
        )

        if filter_status == "📊 แสดงทั้งหมด":
            filtered_df = df
        else:
            filtered_df = df[df['สถานะ Q1'] == filter_status]

        st.dataframe(
            filtered_df[['ตัวชี้วัด', 'เป้าหมาย', 'ปี 69 (Q1)', 'สถานะ Q1']],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # ==========================================
    # 📌 ส่วนการแสดงผลกราฟ และ บทวิเคราะห์ (แบบซ้าย-ขวา)
    # ==========================================
    target_display = str(kpi_data.get('เป้าหมาย', 'ไม่ระบุ'))
    st.markdown(
        f"<h4 style='color: #333;'>📈 SAR ตอนที่ IV ผลการดำเนินการ: {selected_kpi} <span style='color: #D32F2F; font-size: 18px;'>(เป้าหมาย: {target_display})</span></h4>",
        unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # 🎯 แบ่งหน้าจอเป็น 2 ฝั่ง (กราฟ 60% : บทวิเคราะห์ 40%)
    col_chart, col_analysis = st.columns([6, 4])

    with col_chart:
        cols_in_sheet = ['ปี 65', 'ปี 66', 'ปี 67', 'ปี 68', 'ปี 69 (Q1)']
        x_positions = [1, 2, 3, 4, 5]
        x_labels = ['2565', '2566', '2567', '2568', '2569 (Q1)']

        values = []
        text_labels = []

        for col in cols_in_sheet:
            raw_val = kpi_data.get(col)
            num, lbl = extract_plot_data(raw_val)
            values.append(num)
            text_labels.append(lbl)

        fig = go.Figure()

        valid_values = [v for v in values if v is not None]
        max_data_val = max(valid_values) if valid_values else 1

        target_val = 0
        if 'เป้าหมาย' in df.columns and pd.notna(kpi_data['เป้าหมาย']):
            parsed_target, _ = extract_plot_data(str(kpi_data['เป้าหมาย']))
            if parsed_target is not None:
                target_val = parsed_target
                fig.add_hline(y=target_val, line_dash="dash", line_color="red", line_width=2,
                              annotation_text=f"เป้าหมาย", annotation_position="bottom right",
                              annotation_font=dict(family="TH Sarabun New", size=21, color="red"))

        y_max_limit = max(max_data_val, target_val)
        y_max_limit = y_max_limit * 1.25 if y_max_limit > 0 else 100

        shadow_x = [x + 0.015 for x in x_positions]
        shadow_y = [v - (y_max_limit * 0.007) if v is not None else None for v in values]
        fig.add_trace(go.Scatter(
            x=shadow_x, y=shadow_y, mode='lines+markers',
            line=dict(color='rgba(0,0,0,0.18)', width=6),
            marker=dict(size=14, color='rgba(0,0,0,0.18)'),
            hoverinfo='skip', connectgaps=True
        ))

        fig.add_trace(go.Scatter(
            x=x_positions, y=values, mode='lines+markers',
            line=dict(color='#111111', width=5),
            marker=dict(size=14, color='white', line=dict(color='#111111', width=3)),
            connectgaps=True
        ))

        fig.add_trace(go.Scatter(
            x=x_positions, y=values, mode='lines',
            line=dict(color='rgba(255,255,255,0.4)', width=1.5),
            hoverinfo='skip', connectgaps=True
        ))

        if y_max_limit <= 2:
            major_dtick = 0.5
        elif y_max_limit <= 5:
            major_dtick = 1.0
        elif y_max_limit <= 10:
            major_dtick = 2.0
        elif y_max_limit <= 25:
            major_dtick = 5.0
        elif y_max_limit <= 50:
            major_dtick = 10.0
        elif y_max_limit <= 100:
            major_dtick = 20.0
        else:
            major_dtick = round((y_max_limit / 5) / 10) * 10 or 10
        minor_dtick = major_dtick / 5.0

        for x_pos, y, txt in zip(x_positions, values, text_labels):
            if y is not None and txt != "":
                fig.add_annotation(
                    x=x_pos, y=y, text=f"<b>{txt}</b>",
                    showarrow=False, yshift=30,
                    bgcolor="rgba(255, 255, 255, 0.85)",
                    bordercolor="rgba(150, 150, 150, 0.5)", borderwidth=1, borderpad=3,
                    font=dict(family="TH Sarabun New, Tahoma", size=21, color="black")
                )

        fig.update_layout(
            height=550,  # ปรับความสูงให้พอดีกับคอลัมน์
            autosize=True,  # 🎯 ให้ขยายกว้างเต็มพื้นที่ 60% อัตโนมัติ
            font=dict(family="TH Sarabun New, Tahoma, sans-serif", size=21, color="black"),
            xaxis=dict(
                tickmode='array', tickvals=x_positions, ticktext=x_labels,
                range=[0.5, 5.5],
                title=dict(text='ปีงบประมาณ', font=dict(size=28, color="black")),
                tickfont=dict(size=21, color="black"),
                showline=True, linewidth=1, linecolor='black', mirror=True
            ),
            yaxis=dict(
                title=dict(text='ค่าผลลัพธ์ (%)', font=dict(size=28, color="black")),
                tickfont=dict(size=21, color="black"),
                rangemode='tozero', range=[0, y_max_limit],
                showline=True, linewidth=1, linecolor='black', mirror=True,
                showgrid=True, gridcolor='#CCCCCC', gridwidth=1, dtick=major_dtick,
                minor=dict(showgrid=True, gridcolor='#EEEEEE', gridwidth=1, dtick=minor_dtick)
            ),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=40)
        )

        config = {'toImageButtonOptions': {'format': 'png', 'filename': f'KPI_Chart_{selected_kpi}', 'height': 600,
                                           'width': 800, 'scale': 2}, 'displayModeBar': True}
        # 🎯 ใช้ use_container_width=True เพื่อให้กราฟยืดพอดีกับพื้นที่คอลัมน์
        st.plotly_chart(fig, use_container_width=True, config=config)

    with col_analysis:
        if 'วิเคราะห์' in df.columns:
            analysis_text = kpi_data['วิเคราะห์']
            if pd.notna(analysis_text) and str(analysis_text).strip() != '':
                # 🎯 สร้างกล่องตกแต่งแบบ HTML คล้ายฟอร์มรายงาน SAR
                st.markdown(f"""
                <div style="background-color: #F8F9FA; padding: 25px; border-radius: 8px; border: 1px solid #E0E0E0; height: 100%; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);">
                    <h5 style="color: #2C3E50; border-bottom: 2px solid #3498DB; padding-bottom: 10px; margin-top: 0; font-weight: bold;">
                        📝 การวิเคราะห์และ PDCA
                    </h5>
                    <p style="font-size: 16px; line-height: 1.6; color: #444; white-space: pre-wrap; margin-top: 15px;">{analysis_text}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("ยังไม่ได้ระบุข้อมูลการวิเคราะห์สำหรับตัวชี้วัดนี้ในระบบ")

    st.divider()
    with st.expander("ดูตารางข้อมูลต้นฉบับ (Data Table)"):
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("❌ เกิดข้อผิดพลาดในการประมวลผล")
    st.info(f"รายละเอียด: {e}")
