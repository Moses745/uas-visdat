"""
utils/visualizations.py
Modul generator visualisasi interaktif Plotly:
- Geospatial (Choropleth Map 38 Provinsi via px.choropleth_map & Bar Chart Absolut)
- Multivariate (Scatterplot interaktif dengan animasi morphing & anotasi, PCA Biplot, Scree Plot, Parallel Coordinates, Heatmap Korelasi)
- Hierarchical (Treemap & Sunburst 3-Level dengan ukuran agregat aditif)
Proyek UAS Visualisasi Data dan Informasi - Politeknik Statistika STIS
"""

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from .preprocessing import INDICATOR_METADATA

# Palet warna ramah buta warna untuk 7 Pulau/Wilayah (ColorBrewer Okabe-Ito / Dark2)
COLOR_PALETTE_WILAYAH = {
    'Sumatera': '#2b5c8f',             # Deep Blue
    'Jawa': '#d95f02',                 # Vermilion / Rust
    'Bali & Nusa Tenggara': '#7570b3', # Purple / Muted Violet
    'Kalimantan': '#1b9e77',           # Teal / Sea Green
    'Sulawesi': '#e6ab02',             # Amber / Warm Gold
    'Maluku': '#a6761d',               # Bronze / Earth
    'Papua': '#e7298a'                 # Magenta / Crimson
}

# Palet ramah buta warna untuk 4 Tipologi Klaster
COLOR_PALETTE_KLASTER = {
    'K1: Berkembang Sedang': '#2b5c8f',          # Steel Blue
    'K2: Tantangan Struktural (DOB)': '#d95f02',    # Vermilion
    'K3: Sentra Ekonomi Maju': '#1b9e77',       # Teal Green
    'K4: Transisi Kerja / TPT Tinggi': '#7570b3'    # Muted Purple
}

# Pusat dan Zoom Otomatis per Pulau (Bounding Box Indonesia)
PULAU_CAMERA_MAP = {
    'Semua Wilayah (38 Provinsi)': {'lat': -2.2, 'lon': 118.0, 'zoom': 3.85},
    'Sumatera': {'lat': 0.5, 'lon': 101.5, 'zoom': 4.8},
    'Jawa': {'lat': -7.4, 'lon': 110.2, 'zoom': 5.8},
    'Bali & Nusa Tenggara': {'lat': -8.6, 'lon': 119.5, 'zoom': 5.8},
    'Kalimantan': {'lat': -0.2, 'lon': 114.0, 'zoom': 4.9},
    'Sulawesi': {'lat': -1.8, 'lon': 121.5, 'zoom': 5.0},
    'Maluku': {'lat': -3.2, 'lon': 128.5, 'zoom': 5.3},
    'Papua': {'lat': -3.8, 'lon': 137.5, 'zoom': 4.9}
}

# Transisi bawaan Plotly (Plotly.react) hanya berjalan jika SEMUA atribut yang berubah dapat dianimasikan;
# judul/subjudul/nama sumbu yang ikut berubah membuatnya sering tidak jalan. Karena itu animasi saat filter
# berganti ditangani assets/story.js (morph titik, batang tumbuh, cascade, fokus). Durasi 0 mencegah
# gerakan ganda. Ubah ke mis. 650 jika ingin mengaktifkan kembali transisi bawaan Plotly.
NATIVE_TRANSITION_MS = 0

FONT_FAMILY = "Plus Jakarta Sans, Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"


def apply_common_layout(fig, title="", subtitle="", height=550):
    """
    Menerapkan styling tata letak standar akademik STIS pada figure Plotly:
    tipografi konsisten dan whitespace proporsional. Animasi saat filter berganti dikendalikan assets/story.js.
    Catatan: Keterangan sumber pada setiap grafik dihapus sesuai permintaan agar tidak menumpuk dengan sumbu;
    sumber resmi dicantumkan terpadu pada footer aplikasi.
    """
    full_title = f"<b>{title}</b>"
    if subtitle:
        full_title += f"<br><span style='font-size:12px; font-weight:normal; color:#64748b;'>{subtitle}</span>"
        
    fig.update_layout(
        title={
            'text': full_title,
            'y': 0.96,
            'x': 0.02,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': {'family': FONT_FAMILY, 'size': 16, 'color': '#0f172a'}
        },
        font={'family': FONT_FAMILY, 'color': '#334155'},
        height=height,
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(248,250,252,0.6)',
        margin=dict(l=55, r=35, t=75, b=55),
        uirevision="constant",  # Kunci agar Plotly.react memicu transisi gerak titik/batang alih-alih reset
        transition={
            'duration': NATIVE_TRANSITION_MS,
            'easing': 'cubic-in-out'
        }
    )
    return fig


def plot_choropleth_map(df, geojson_data, indicator_col, selected_pulau="Semua Wilayah (38 Provinsi)", map_style="carto-positron"):
    """
    Membuat Peta Choropleth Interaktif 38 Provinsi Indonesia via px.choropleth_map.
    Mendukung auto-centering per pulau dan skala warna global konsisten.
    """
    meta = INDICATOR_METADATA.get(indicator_col, {
        'label': indicator_col,
        'unit': '',
        'format': ':.2f',
        'direction': 'higher_better',
        'cmap': 'Viridis',
        'desc': ''
    })
    
    if meta['direction'] == 'lower_better':
        colorscale = 'YlOrRd'
    else:
        colorscale = 'Viridis' if indicator_col != 'PDRB_per_Kapita_HB_2025_ribu_Rp' else 'Plasma'
        
    global_min = float(df[indicator_col].min())
    global_max = float(df[indicator_col].max())
    cam = PULAU_CAMERA_MAP.get(selected_pulau, PULAU_CAMERA_MAP['Semua Wilayah (38 Provinsi)'])
    
    df_plot = df.copy()

    custom_data = [
        'Provinsi',
        'Pulau_Wilayah',
        indicator_col,
        'IPM_2025',
        'Kemiskinan_September_2025_persen',
        'PDRB_per_Kapita_HB_2025_ribu_Rp',
        'TPT_Agustus_2025_persen'
    ]

	# Pastikan nama kolom unik sebelum diproses Plotly/Narwhals
    df_plot = df_plot.loc[:, ~df_plot.columns.duplicated()].copy()

    try:
        fig = px.choropleth_map(
            df_plot,
            geojson=geojson_data,
            locations='Provinsi_Geo',
            featureidkey='properties.PROVINSI',
            color=indicator_col,
            color_continuous_scale=colorscale,
            range_color=[global_min, global_max],
            map_style=map_style,
            center={"lat": cam['lat'], "lon": cam['lon']},
            zoom=cam['zoom'],
            opacity=0.88,
            hover_name='Provinsi',
            custom_data=custom_data
        )
    except AttributeError:
        fig = px.choropleth_mapbox(
            df_plot,
            geojson=geojson_data,
            locations='Provinsi_Geo',
            featureidkey='properties.PROVINSI',
            color=indicator_col,
            color_continuous_scale=colorscale,
            range_color=[global_min, global_max],
            mapbox_style=map_style,
            center={"lat": cam['lat'], "lon": cam['lon']},
            zoom=cam['zoom'],
            opacity=0.88,
            hover_name='Provinsi',
            custom_data=custom_data
        )

    unit_str = f" ({meta['unit']})" if meta['unit'] else ""
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "<i>Wilayah: %{customdata[1]}</i><br>"
            f"<b>{meta['label']}:</b> %{{customdata[2]:,.2f}}{unit_str}<br>"
            "<hr style='margin:4px 0;'>"
            "<b>IPM 2025:</b> %{customdata[3]:.2f}<br>"
            "<b>Kemiskinan:</b> %{customdata[4]:.2f}%<br>"
            "<b>PDRB per Kapita:</b> Rp %{customdata[5]:,.0f} ribu<br>"
            "<b>TPT:</b> %{customdata[6]:.2f}%"
            "<extra></extra>"
        )
    )
    
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=dict(
                text=f"<b>{meta['unit']}</b>" if meta['unit'] else "<b>Nilai</b>",
                font=dict(size=12, family=FONT_FAMILY)
            ),
            thickness=14,
            len=0.75,
            x=1.01,
            y=0.5
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=560
    )
    
    sub_title = f"Visualisasi tematik 38 provinsi di Indonesia (Satuan: {meta['unit']})"
    if selected_pulau != "Semua Wilayah (38 Provinsi)":
        sub_title += f" • <i>Menyorot Pulau: {selected_pulau}</i>"
        
    apply_common_layout(
        fig,
        title=f"Distribusi Spasial: {meta['label']}",
        subtitle=sub_title,
        height=560
    )
    return fig


def plot_absolute_bar_comparison(df, col='PDRB_Total_ADHK_2025_miliar_Rp', selected_pulau="Semua Wilayah (38 Provinsi)"):
    """
    Visualisasi diagram batang horizontal terurut untuk variabel absolut.
    - Menampilkan seluruh 38 provinsi dalam konteks lengkap.
    - Menggunakan ids=Provinsi agar perubahan filter/metrik memicu animasi perpanjangan/pemendekan batang secara mulus.
    - Tombol 'Putar Batang' dihapus agar antarmuka bersih dan rapi.
    """
    meta = INDICATOR_METADATA.get(col, {'label': col, 'unit': ''})
    df_sorted = df.sort_values(by=col, ascending=True).copy()
    
    colors = []
    opacities = []
    for _, row in df_sorted.iterrows():
        p = row['Pulau_Wilayah']
        if selected_pulau == "Semua Wilayah (38 Provinsi)" or p == selected_pulau:
            colors.append(COLOR_PALETTE_WILAYAH.get(p, '#2563eb'))
            opacities.append(1.0)
        else:
            colors.append('#cbd5e1')
            opacities.append(0.35)
            
    fig = go.Figure()

    # Batang Utama dengan identitas ids tetap untuk morphing animasi
    fig.add_trace(go.Bar(
        y=df_sorted['Provinsi'],
        x=df_sorted[col],
        ids=df_sorted['Provinsi'],
        orientation='h',
        marker=dict(
            color=colors,
            opacity=opacities,
            line=dict(color='rgba(255,255,255,0.7)', width=0.8)
        ),
        customdata=np.stack((df_sorted['Provinsi'], df_sorted['Pulau_Wilayah'], df_sorted[col]), axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            f"{meta['label']}: %{{customdata[2]:,.1f}} {meta['unit']}"
            "<extra></extra>"
        ),
        text=[f"{v:,.0f}" if v > 1000 else f"{v:,.1f}" for v in df_sorted[col]],
        textposition='outside',
        textfont=dict(size=11, family=FONT_FAMILY)
    ))

    chart_height = max(550, len(df_sorted) * 22)
    sub = f"Peringkat perbandingan besaran absolut 38 provinsi (Satuan: {meta['unit']})"
    if selected_pulau != "Semua Wilayah (38 Provinsi)":
        sub += f" • <i>Menyorot Pulau: {selected_pulau}</i>"

    fig.update_layout(
        xaxis_title=f"{meta['label']} ({meta['unit']})",
        yaxis_title="",
        xaxis=dict(range=[0, df_sorted[col].max() * 1.18]),
        margin=dict(l=145, r=40, t=65, b=45)
    )

    apply_common_layout(
        fig,
        title=f"Perbandingan Nilai Absolut: {meta['label']}",
        subtitle=sub,
        height=chart_height
    )
    return fig


def plot_bivariate_scatter(df, x_col, y_col, selected_pulau="Semua Wilayah (38 Provinsi)", add_trendline=True):
    """
    Membuat Scatterplot Interaktif dengan transisi pergerakan titik (morphing animation).
    - Memakai satu trace terpadu dengan ids=Provinsi agar Plotly dapat menganimasikan pergeseran posisi titik (X, Y) secara nyata saat variabel diganti.
    - Nama sumbu rapi, terpisah, dan tidak bertabrakan.
    """
    meta_x = INDICATOR_METADATA[x_col]
    meta_y = INDICATOR_METADATA[y_col]
    
    is_same_var = (x_col == y_col)
    n_points = len(df)
    
    fig = go.Figure()
    
    if is_same_var:
        fig.add_annotation(
            text="⚠️ Variabel Sumbu X dan Y sama. Pilih dua variabel berbeda untuk memeriksa korelasi.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#b91c1c", family=FONT_FAMILY),
            bgcolor="rgba(254, 242, 242, 0.9)",
            bordercolor="#f87171", borderpad=10
        )
        apply_common_layout(fig, title=f"Hubungan Bivariat: {meta_x['label']} vs {meta_y['label']}", height=560)
        return fig
        
    if n_points < 3:
        fig.add_annotation(
            text="ℹ️ Data terlalu sedikit untuk korelasi/tren (minimal 3 observasi)",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#475569", family=FONT_FAMILY),
            bgcolor="rgba(241, 245, 249, 0.9)",
            borderpad=8
        )
        apply_common_layout(fig, title=f"Hubungan Bivariat: {meta_x['label']} vs {meta_y['label']}", height=560)
        return fig

    corr_val = df[x_col].corr(df[y_col])
    r2_val = corr_val ** 2 if np.isfinite(corr_val) else 0.0

    # Menyiapkan warna dan ukuran per titik dengan pelacakan ID provinsi
    colors = []
    opacities = []
    sizes = []
    for _, row in df.iterrows():
        p = row['Pulau_Wilayah']
        is_focus = (selected_pulau == "Semua Wilayah (38 Provinsi)" or selected_pulau == p)
        colors.append(COLOR_PALETTE_WILAYAH.get(p, '#475569') if is_focus else '#94a3b8')
        opacities.append(0.92 if is_focus else 0.22)
        sizes.append(13 if is_focus else 8)

    # 1. Trace Utama Titik Scatter (Single Trace dengan IDs untuk animasi transisi)
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        ids=df['Provinsi'],  # Kunci esensial agar Plotly menganimasikan pergerakan titik
        mode='markers',
        name='Provinsi',
        showlegend=False,
        marker=dict(
            size=sizes,
            color=colors,
            opacity=opacities,
            line=dict(width=1.2, color='#ffffff')
        ),
        customdata=np.stack((
            df['Provinsi'], df['Pulau_Wilayah'],
            df[x_col], df[y_col],
            df['IPM_2025'], df['Kemiskinan_September_2025_persen']
        ), axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            f"<b>{meta_x['label']}:</b> %{{customdata[2]:,.2f}} {meta_x['unit']}<br>"
            f"<b>{meta_y['label']}:</b> %{{customdata[3]:,.2f}} {meta_y['unit']}<br>"
            "<hr style='margin:4px 0;'>"
            "<b>IPM:</b> %{customdata[4]:.2f} | <b>Kemiskinan:</b> %{customdata[5]:.2f}%"
            "<extra></extra>"
        )
    ))

    # Trace Dummy untuk Legenda Pulau yang Rapi
    for p_name, p_col in COLOR_PALETTE_WILAYAH.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=p_name,
            marker=dict(size=10, color=p_col),
            showlegend=True
        ))

    # Garis Tren Linear OLS
    if add_trendline and np.isfinite(corr_val):
        x_vals = df[x_col].values
        y_vals = df[y_col].values
        valid_mask = np.isfinite(x_vals) & np.isfinite(y_vals)
        if valid_mask.sum() > 2:
            poly = np.polyfit(x_vals[valid_mask], y_vals[valid_mask], deg=1)
            x_line = np.linspace(x_vals[valid_mask].min(), x_vals[valid_mask].max(), 100)
            y_line = np.polyval(poly, x_line)
            
            fig.add_trace(go.Scatter(
                x=x_line,
                y=y_line,
                mode='lines',
                name='Garis Tren (OLS)',
                line=dict(color='#475569', width=2, dash='dash'),
                hoverinfo='skip'
            ))

    # Anotasi Provinsi Sorotan Bab 5 (DKI, DIY, Bali, Papua Tengah)
    highlight_provinces = {
        'DKI Jakarta': "DKI Jakarta",
        'DI Yogyakarta': "DIY",
        'Bali': "Bali",
        'Papua Tengah': "Papua Tengah"
    }
    for prov_name, note in highlight_provinces.items():
        prov_row = df[df['Provinsi'] == prov_name]
        if not prov_row.empty:
            px_val = prov_row[x_col].values[0]
            py_val = prov_row[y_col].values[0]
            fig.add_annotation(
                x=px_val,
                y=py_val,
                text=f"<b>{prov_name}</b>",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1.2,
                arrowcolor="#0f172a",
                ax=22,
                ay=-22,
                font=dict(size=10, family=FONT_FAMILY, color="#0f172a"),
                bgcolor="rgba(255, 255, 255, 0.88)",
                bordercolor="#cbd5e1",
                borderwidth=1,
                borderpad=3
            )

    # Garis Rata-rata Nasional
    fig.add_vline(x=df[x_col].mean(), line_width=1, line_dash='dot', line_color='#94a3b8',
                  annotation_text="Rata-rata X", annotation_position="top right")
    fig.add_hline(y=df[y_col].mean(), line_width=1, line_dash='dot', line_color='#94a3b8',
                  annotation_text="Rata-rata Y", annotation_position="bottom right")

    # Range sumbu tetap dari seluruh 38 provinsi
    x_pad = (df[x_col].max() - df[x_col].min()) * 0.08
    y_pad = (df[y_col].max() - df[y_col].min()) * 0.08
    fig.update_xaxes(
        range=[df[x_col].min() - x_pad, df[x_col].max() + x_pad], 
        title=dict(text=f"<b>{meta_x['label']}</b> ({meta_x['unit']})", font=dict(size=12))
    )
    fig.update_yaxes(
        range=[df[y_col].min() - y_pad, df[y_col].max() + y_pad], 
        title=dict(text=f"<b>{meta_y['label']}</b> ({meta_y['unit']})", font=dict(size=12))
    )

    strength = "Sangat Kuat" if abs(corr_val) > 0.7 else "Kuat" if abs(corr_val) > 0.5 else "Sedang" if abs(corr_val) > 0.3 else "Lemah"
    arah = "Positif" if corr_val > 0 else "Negatif"
    sub = f"Koefisien Korelasi Pearson (r) = {corr_val:+.3f} ({strength} {arah}) | R² = {r2_val:.3f}"
    if selected_pulau != "Semua Wilayah (38 Provinsi)":
        sub += f" • <i>Menyorot Pulau: {selected_pulau}</i>"

    fig.update_layout(
        legend_title_text="Pulau / Wilayah",
        margin=dict(l=65, r=40, t=75, b=60)
    )

    apply_common_layout(
        fig,
        title=f"Hubungan Bivariat: {meta_x['label']} vs {meta_y['label']}",
        subtitle=sub,
        height=570
    )
    return fig


def plot_pca_biplot(pca_df, loadings_df, var_pc1, var_pc2, selected_pulau="Semua Wilayah (38 Provinsi)", pc1_label=None, pc2_label=None):
    """
    Membuat PCA Biplot interaktif:
    - Nama sumbu ringkas, elegan, dan tidak bertabrakan dengan angka tick.
    - Keterangan sumber dihapus agar margin bawah bersih.
    - Titik-titik memiliki IDs agar animasi morphing berjalan mulus saat mengganti filter.
    """
    fig = go.Figure()

    colors = []
    opacities = []
    sizes = []
    for _, row in pca_df.iterrows():
        p = row['Pulau_Wilayah']
        is_focus = (selected_pulau == "Semua Wilayah (38 Provinsi)" or selected_pulau == p)
        colors.append(COLOR_PALETTE_WILAYAH.get(p, '#475569') if is_focus else '#94a3b8')
        opacities.append(0.92 if is_focus else 0.20)
        sizes.append(13 if is_focus else 8)

    # Titik Provinsi Utama dengan ids untuk transisi gerak
    fig.add_trace(go.Scatter(
        x=pca_df['PC1'],
        y=pca_df['PC2'],
        ids=pca_df['Provinsi'],
        mode='markers',
        name='Provinsi',
        showlegend=False,
        marker=dict(
            size=sizes,
            color=colors,
            opacity=opacities,
            line=dict(width=1.2, color='#ffffff')
        ),
        customdata=np.stack((
            pca_df['Provinsi'], pca_df['Pulau_Wilayah'],
            pca_df['IPM_2025'], pca_df['PDRB_per_Kapita_HB_2025_ribu_Rp']
        ), axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            "<b>PC1:</b> %{x:.2f}<br>"
            "<b>PC2:</b> %{y:.2f}<br>"
            "<b>IPM:</b> %{customdata[2]:.2f}<br>"
            "<b>PDRB/Kapita:</b> Rp %{customdata[3]:,.0f} ribu"
            "<extra></extra>"
        )
    ))

    # Dummy trace untuk legenda pulau
    for p_name, p_col in COLOR_PALETTE_WILAYAH.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=p_name,
            marker=dict(size=10, color=p_col),
            showlegend=True
        ))

    # Skala vektor loading agar proporsional
    scale_factor = max(abs(pca_df['PC1']).max(), abs(pca_df['PC2']).max()) * 0.75
    
    for idx, row in loadings_df.iterrows():
        vx = row['PC1_Component'] * scale_factor
        vy = row['PC2_Component'] * scale_factor
        
        fig.add_trace(go.Scatter(
            x=[0, vx],
            y=[0, vy],
            mode='lines+markers',
            line=dict(color='#dc2626', width=1.5),
            marker=dict(size=[0, 5], color='#dc2626'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_annotation(
            x=vx,
            y=vy,
            text=f"<b>{row['Indikator']}</b>",
            showarrow=False,
            font=dict(size=9, color='#991b1b', family=FONT_FAMILY),
            yshift=6 if vy >= 0 else -6,
            xshift=6 if vx >= 0 else -6
        )

    # Anotasi Provinsi Kunci (DKI, DIY, Bali, Papua Tengah, Papua Pegunungan)
    key_provs = ['DKI Jakarta', 'DI Yogyakarta', 'Bali', 'Papua Tengah', 'Papua Pegunungan']
    for kp in key_provs:
        kp_row = pca_df[pca_df['Provinsi'] == kp]
        if not kp_row.empty:
            fig.add_annotation(
                x=kp_row['PC1'].values[0],
                y=kp_row['PC2'].values[0],
                text=f"<b>{kp}</b>",
                showarrow=True,
                arrowhead=1,
                arrowwidth=1.2,
                arrowcolor="#0f172a",
                ax=20,
                ay=-20,
                font=dict(size=9.5, color="#0f172a", family=FONT_FAMILY),
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#cbd5e1",
                borderpad=2
            )

    fig.add_hline(y=0, line_width=1, line_color='#cbd5e1')
    fig.add_vline(x=0, line_width=1, line_color='#cbd5e1')
    
    # Nama sumbu yang ringkas dan terstruktur (tidak bertabrakan)
    fig.update_layout(
        xaxis_title=f"<b>PC1 ({var_pc1:.1f}% Varians)</b>: Kesejahteraan vs Deprivasi",
        yaxis_title=f"<b>PC2 ({var_pc2:.1f}% Varians)</b>: Aglomerasi & Pasar Kerja",
        legend_title_text="Pulau / Wilayah",
        margin=dict(l=75, r=40, t=75, b=65)
    )
    
    sub = f"Reduksi dimensi data 38 provinsi. Total varians 2 PC = {(var_pc1 + var_pc2):.1f}%"
    if selected_pulau != "Semua Wilayah (38 Provinsi)":
        sub += f" • <i>Menyorot Pulau: {selected_pulau}</i>"

    apply_common_layout(
        fig,
        title="PCA Biplot: Peta Posisi Multidimensi & Vektor Indikator",
        subtitle=sub,
        height=620
    )
    return fig


def plot_cluster_scatter(cluster_df, selected_pulau="Semua Wilayah (38 Provinsi)"):
    """
    Visualisasi sebaran tipologi klaster K-Means (k=4) ramah buta warna.
    Menggunakan IDs untuk pergerakan transisi dinamis.
    """
    color_col = 'Tipologi_Klaster_Singkat' if 'Tipologi_Klaster_Singkat' in cluster_df.columns else 'Tipologi_Klaster'
    
    fig = go.Figure()

    colors = []
    opacities = []
    sizes = []
    for _, row in cluster_df.iterrows():
        is_focus = (selected_pulau == "Semua Wilayah (38 Provinsi)" or row['Pulau_Wilayah'] == selected_pulau)
        tipologi = row[color_col]
        tip_color = COLOR_PALETTE_KLASTER.get(tipologi, '#475569')
        colors.append(tip_color if is_focus else '#94a3b8')
        opacities.append(0.90 if is_focus else 0.20)
        marker_size = max(10, min(36, np.sqrt(row['PDRB_per_Kapita_HB_2025_ribu_Rp']) / 14))
        sizes.append(marker_size if is_focus else max(6, marker_size * 0.6))

    fig.add_trace(go.Scatter(
        x=cluster_df['IPM_2025'],
        y=cluster_df['Kemiskinan_September_2025_persen'],
        ids=cluster_df['Provinsi'],
        mode='markers',
        name='Provinsi',
        showlegend=False,
        marker=dict(
            size=sizes,
            color=colors,
            opacity=opacities,
            line=dict(width=1.2, color='#ffffff')
        ),
        customdata=np.stack((
            cluster_df['Provinsi'], cluster_df['Pulau_Wilayah'],
            cluster_df['Tipologi_Klaster'],
            cluster_df['IPM_2025'], cluster_df['Kemiskinan_September_2025_persen'],
            cluster_df['PDRB_per_Kapita_HB_2025_ribu_Rp']
        ), axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
            "<b>Tipologi:</b> %{customdata[2]}<br>"
            "<hr style='margin:4px 0;'>"
            "<b>IPM:</b> %{customdata[3]:.2f}<br>"
            "<b>Kemiskinan:</b> %{customdata[4]:.2f}%<br>"
            "<b>PDRB per Kapita:</b> Rp %{customdata[5]:,.0f} ribu"
            "<extra></extra>"
        )
    ))

    # Dummy trace untuk legenda 4 tipologi
    for tip, col in COLOR_PALETTE_KLASTER.items():
        if tip in cluster_df[color_col].values:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                name=tip,
                marker=dict(size=12, color=col),
                showlegend=True
            ))

    fig.update_layout(
        xaxis_title="<b>Indeks Pembangunan Manusia (IPM 2025)</b>",
        yaxis_title="<b>Tingkat Kemiskinan (%)</b>",
        legend_title_text="Tipologi Klaster (k=4)",
        margin=dict(l=65, r=40, t=75, b=60)
    )
    
    sub = "Ukuran lingkaran proporsional dengan PDRB per kapita. Warna membedakan 4 tipologi hasil K-Means."
    if selected_pulau != "Semua Wilayah (38 Provinsi)":
        sub += f" • <i>Menyorot Pulau: {selected_pulau}</i>"

    apply_common_layout(
        fig,
        title="Tipologi Wilayah Pembangunan (K-Means Clustering, k=4)",
        subtitle=sub,
        height=520
    )
    return fig


def plot_pca_variance_bars(pca_model, feature_cols):
    """
    Scree plot visualisasi explained variance untuk setiap komponen utama.
    """
    n_comp = len(pca_model.explained_variance_ratio_)
    pc_names = [f"PC{i+1}" for i in range(n_comp)]
    exp_var = pca_model.explained_variance_ratio_ * 100
    cum_var = np.cumsum(exp_var)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=pc_names,
        y=exp_var,
        name='Explained Variance (%)',
        marker_color='#0284c7',
        text=[f"{v:.1f}%" for v in exp_var],
        textposition='outside'
    ))
    
    fig.add_trace(go.Scatter(
        x=pc_names,
        y=cum_var,
        name='Kumulatif (%)',
        mode='lines+markers+text',
        marker=dict(color='#059669', size=8),
        line=dict(color='#059669', width=2),
        text=[f"{c:.1f}%" for c in cum_var],
        textposition='top center',
        yaxis='y2'
    ))
    
    fig.update_layout(
        yaxis=dict(title='Varians Terjelaskan (%)', range=[0, max(exp_var) * 1.25]),
        yaxis2=dict(
            title='Varians Kumulatif (%)',
            range=[0, 105],
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0.02, y=0.98),
        margin=dict(l=50, r=60, t=70, b=50)
    )
    
    apply_common_layout(
        fig,
        title="Scree Plot: Kontribusi Varians Tiap Komponen Utama",
        subtitle=f"Dihitung dari {len(feature_cols)} indikator sosial-ekonomi terstandarisasi",
        height=450
    )
    return fig


def plot_parallel_coordinates(df, feature_cols=None):
    """
    Visualisasi Parallel Coordinates untuk profil multidimensi 38 provinsi.
    Label sumbu disingkat rapi dan margin atas diperlebar agar tidak saling menimpa.
    """
    if feature_cols is None:
        feature_cols = [
            'IPM_2025',
            'PDRB_per_Kapita_HB_2025_ribu_Rp',
            'Kemiskinan_September_2025_persen',
            'TPT_Agustus_2025_persen',
            'TPAK_Agustus_2025_persen',
            'TPK_Hotel_Berbintang_2025_persen'
        ]
        
    # Label ringkas dan jelas agar tidak bertabrakan secara horizontal
    SHORT_PAR_LABELS = {
        'IPM_2025': 'IPM',
        'PDRB_per_Kapita_HB_2025_ribu_Rp': 'PDRB/Kapita',
        'Kemiskinan_September_2025_persen': 'Kemiskinan (%)',
        'TPT_Agustus_2025_persen': 'TPT (%)',
        'TPAK_Agustus_2025_persen': 'TPAK (%)',
        'TPK_Hotel_Berbintang_2025_persen': 'TPK Hotel (%)'
    }

    dimensions = []
    for col in feature_cols:
        dim = dict(
            range=[df[col].min(), df[col].max()],
            label=SHORT_PAR_LABELS.get(col, col),
            values=df[col]
        )
        dimensions.append(dim)
        
    fig = go.Figure(data=
        go.Parcoords(
            line=dict(
                color=df['IPM_2025'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="<b>IPM 2025</b>", thickness=14)
            ),
            dimensions=dimensions
        )
    )
    
    # Margin atas diperlebar (t=105) agar judul & subjudul tidak menabrak label sumbu
    fig.update_layout(
        margin=dict(l=60, r=60, t=105, b=40)
    )

    apply_common_layout(
        fig,
        title="Parallel Coordinates: Profil Multidimensi Pembangunan Provinsi",
        #subtitle="Tarik dan geser kursor pada sumbu vertikal untuk menapis rentang nilai (brushing)",
        height=540
    )
    
    return fig


def plot_treemap(df, size_col='PDRB_Total_ADHK_2025_miliar_Rp', color_col='IPM_2025'):
    """
    Visualisasi Hierarki 3-Level Menggunakan Treemap:
    Indonesia -> Pulau/Wilayah -> Provinsi.
    Ukuran = Variabel Agregat Aditif, Warna = IPM.
    """
    meta_size = INDICATOR_METADATA.get(size_col, {'label': size_col, 'unit': ''})
    meta_color = INDICATOR_METADATA.get(color_col, {'label': color_col, 'unit': ''})
    
    fig = px.treemap(
        df,
        path=[px.Constant("Indonesia"), 'Hierarki_Level_2', 'Provinsi'],
        values=size_col,
        color=color_col,
        color_continuous_scale='Viridis',
        hover_name='Provinsi',
        custom_data=['Provinsi', 'Pulau_Wilayah', size_col, color_col, 'Kemiskinan_September_2025_persen']
    )
    
    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Parent: %{parent}<br>"
            f"<b>Ukuran ({meta_size['label']}):</b> %{{value:,.0f}} {meta_size['unit']}<br>"
            f"<b>Warna ({meta_color['label']}):</b> %{{color:.2f}} {meta_color['unit']}<br>"
            "<extra></extra>"
        )
    )
    
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=f"<b>{meta_color['label']}</b>",
            thickness=14,
            len=0.75
        ),
        margin=dict(l=20, r=20, t=75, b=20)
    )
    
    apply_common_layout(
        fig,
        title=f"Treemap Hierarkis: Struktur Wilayah Indonesia (Ukuran: {meta_size['label']}, Warna: {meta_color['label']})",
        subtitle="Struktur: Indonesia → Pulau/Wilayah → Provinsi. Klik pada kotak wilayah untuk drill-down.",
        height=600
    )
    return fig


def plot_sunburst(df, size_col='PDRB_Total_ADHK_2025_miliar_Rp', color_col='IPM_2025'):
    """
    Visualisasi Hierarki 3-Level Menggunakan Sunburst:
    Struktur radial konsentris dari pusat Indonesia ke lingkar terluar Provinsi.
    Ukuran = Variabel Agregat Aditif, Warna = IPM.
    """
    meta_size = INDICATOR_METADATA.get(size_col, {'label': size_col, 'unit': ''})
    meta_color = INDICATOR_METADATA.get(color_col, {'label': color_col, 'unit': ''})
    
    fig = px.sunburst(
        df,
        path=[px.Constant("Indonesia"), 'Hierarki_Level_2', 'Provinsi'],
        values=size_col,
        color=color_col,
        color_continuous_scale='Viridis',
        hover_name='Provinsi',
        custom_data=['Provinsi', 'Pulau_Wilayah', size_col, color_col]
    )
    
    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Induk Wilayah: %{parent}<br>"
            f"<b>Ukuran ({meta_size['label']}):</b> %{{value:,.0f}} {meta_size['unit']}<br>"
            f"<b>Warna ({meta_color['label']}):</b> %{{color:.2f}} {meta_color['unit']}<br>"
            "<extra></extra>"
        )
    )
    
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=f"<b>{meta_color['label']}</b>",
            thickness=14,
            len=0.75
        ),
        margin=dict(l=20, r=20, t=75, b=20)
    )
    
    apply_common_layout(
        fig,
        title="Sunburst Hierarkis: Radial Struktur Wilayah Indonesia",
        subtitle="Lingkar Dalam (Indonesia) → Lingkar Tengah (Pulau) → Lingkar Luar (Provinsi). Klik sektor untuk navigasi.",
        height=620
    )
    return fig


def plot_correlation_heatmap(df):
    """
    Membuat Matriks Korelasi Heatmap 9 Indikator Pembangunan Sosial-Ekonomi BPS 2025.
    Menampilkan koefisien korelasi Pearson di setiap sel dengan palet divergen RdBu_r.
    """
    from .analysis import compute_correlation_matrix
    corr_df = compute_correlation_matrix(df)
    
    short_labels = {
        'IPM_2025': 'IPM',
        'PDRB_per_Kapita_HB_2025_ribu_Rp': 'PDRB/Kap',
        'Kemiskinan_September_2025_persen': 'Kemiskinan %',
        'Penduduk_Miskin_September_2025_ribu': 'Jml Miskin',
        'PDRB_Total_ADHK_2025_miliar_Rp': 'PDRB Total',
        'TPT_Agustus_2025_persen': 'TPT %',
        'TPAK_Agustus_2025_persen': 'TPAK %',
        'TPK_Hotel_Berbintang_2025_persen': 'TPK Bintang',
        'TPK_Hotel_Nonbintang_2025_persen': 'TPK Nonbintang'
    }
    
    labels_display = [short_labels.get(c, c) for c in corr_df.columns]
    
    z_vals = corr_df.values
    text_vals = [[f"{val:+.2f}" for val in row] for row in z_vals]
    
    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=labels_display,
        y=labels_display,
        text=text_vals,
        texttemplate="%{text}",
        textfont={"size": 11, "family": FONT_FAMILY},
        colorscale='RdBu_r',
        zmin=-1.0,
        zmax=1.0,
        colorbar=dict(title="<b>r Pearson</b>", thickness=14, len=0.8)
    ))
    
    fig.update_layout(
        margin=dict(l=65, r=40, t=75, b=50),
        xaxis=dict(tickangle=-30),
        height=520
    )
    
    apply_common_layout(
        fig,
        title="Matriks Korelasi Pearson (9 Indikator Sosial-Ekonomi)",
        subtitle="Mengevaluasi derajat keterikatan linier antarindikator makro di 38 provinsi Indonesia",
        height=540
    )
    return fig
