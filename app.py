"""
app.py
Aplikasi Visualisasi Data Interaktif & Data Storytelling (Web Story / Scrollytelling)
"Indonesia 2025: Potret Pembangunan Sosial-Ekonomi"
Proyek UAS Visualisasi Data dan Informasi - Politeknik Statistika STIS
"""

import os
import hashlib
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.preprocessing import (
    load_data, load_geojson, standardize_provinces,
    validate_dataset, INDICATOR_METADATA
)
from utils.analysis import (
    compute_summary_statistics, compute_national_overview_cards,
    compute_correlation_matrix, perform_pca_analysis,
    perform_kmeans_clustering, compute_cluster_validation_metrics,
    get_numeric_indicators
)
from utils.visualizations import (
    plot_choropleth_map, plot_absolute_bar_comparison,
    plot_bivariate_scatter, plot_pca_biplot,
    plot_pca_variance_bars, plot_parallel_coordinates,
    plot_treemap, plot_sunburst, plot_cluster_scatter,
    plot_correlation_heatmap, COLOR_PALETTE_WILAYAH
)

# ---------------------------------------------------------
# 1. KONFIGURASI STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Indonesia 2025: Potret Pembangunan Sosial-Ekonomi",
    page_icon="🇮🇩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeksi CSS Khusus Desain Web Story
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Helper responsif untuk kompatibilitas Streamlit
def render_plotly(fig, key=None):
    """Menampilkan grafik Plotly dengan key stabil agar terpicu transisi halus."""
    try:
        st.plotly_chart(fig, key=key, width="stretch")
    except TypeError:
        st.plotly_chart(fig, key=key, use_container_width=True)

def render_table(df_table, hide_index=True):
    """Menampilkan tabel dataframe dengan lebar penuh bebas pesan deprecation."""
    try:
        st.dataframe(df_table, width="stretch", hide_index=hide_index)
    except TypeError:
        st.dataframe(df_table, use_container_width=True, hide_index=hide_index)


def subchapter_header(num, title, subtitle=""):
    """Header sub-bab beranimasi (chip nomor pop-in, judul slide-in, garis menjalar)."""
    sub = f"<div class='sub-subtitle'>{subtitle}</div>" if subtitle else ""
    sid = num.replace(".", "-")
    st.markdown(
        f"<div class='sub-header reveal' id='bab-{sid}'>"
        f"<div class='sub-num'>{num}</div>"
        f"<div class='sub-text'><div class='sub-title'>{title}</div>{sub}</div>"
        f"<div class='sub-line'></div></div>",
        unsafe_allow_html=True
    )


def chart_sig(name, *parts, fx="focus"):
    """
    Menaruh penanda tak terlihat tepat SEBELUM sebuah grafik/tabel.
    Nilai `data-sig` dihitung dari seluruh filter yang memengaruhi grafik tersebut; saat berubah,
    assets/story.js memainkan animasi pada grafik di bawahnya. Jenis efek (fx):
      'morph'   -> titik scatter bergeser & berubah ukuran ke posisi baru
      'grow'    -> batang tumbuh dari sumbu
      'cascade' -> irisan treemap/sunburst muncul berurutan
      'focus'   -> redup + blur lalu menajam (peta, tabel)
    """
    raw = "|".join(str(p) for p in parts)
    sig = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    st.markdown(
        f"<div class='chart-sig' data-chart='{name}' data-sig='{sig}' data-fx='{fx}'></div>",
        unsafe_allow_html=True
    )


def chapter_opener(num, badge, title, desc):
    """Pembuka bab dengan ubin nomor besar 'BAB n' dan penelusur 5 langkah (n dari 5)."""
    total = 5
    steps = "".join(
        f"<span class='co-step{' on' if i < num else ''}{' cur' if i == num else ''}' style='--i:{i}'></span>"
        for i in range(1, total + 1)
    )
    desc = " ".join(desc.split())
    st.markdown(
        f"<div class='chapter-opener reveal' id='bab-{num}'>"
        f"<div class='chapter-opener-num'>0{num}</div>"
        f"<div class='chapter-opener-body'>"
        f"<div class='co-head'>"
        f"<div class='co-tile'><span class='co-tile-label'>BAB</span><span class='co-tile-num'>{num}</span></div>"
        f"<div class='co-meta'><div class='chapter-badge'>{badge}</div>"
        f"<div class='co-steps'>{steps}<span class='co-of'>Bab {num} dari {total}</span></div></div>"
        f"</div>"
        f"<div class='chapter-title'>{title}</div>"
        f"<div class='chapter-desc'>{desc}</div>"
        f"</div>"
        f"<div class='chapter-opener-line'></div></div>",
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# 2. CACHING DATA (OPTIMASI PERFORMA)
# ---------------------------------------------------------
@st.cache_data
def get_clean_data():
    """Memuat dan membersihkan dataset BPS dengan cache data."""
    df_raw = load_data("data/dataset_sosial_ekonomi.csv")
    df_clean = standardize_provinces(df_raw)
    return df_clean

@st.cache_data
def get_geojson_map():
    """Memuat GeoJSON 38 provinsi dengan cache data."""
    return load_geojson("geojson/indonesia-38-provinces.geojson")

@st.cache_data
def run_cached_pca(df):
    """Menjalankan analisis PCA dengan cache data."""
    return perform_pca_analysis(df)

@st.cache_data
def run_cached_clustering(df):
    """Menjalankan clustering K-Means dengan cache data."""
    return perform_kmeans_clustering(df)

# Pemuatan data dengan penanganan kesalahan
try:
    df = get_clean_data()
    geojson_data = get_geojson_map()
except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat memuat data: {e}")
    st.stop()


# ---------------------------------------------------------
# 3. SIDEBAR: DAFTAR ISI & FILTER RINGKAS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 Navigasi Bab Cerita")
    st.markdown("""
    <div id='toc-navigation-box' style='display:flex; flex-direction:column; gap:4px;'>
        <a class='toc-link active' href='#bab-1'>📖 Bab 1: Lanskap Makro</a>
        <a class='toc-link' href='#bab-2'>🗺️ Bab 2: Dimensi Spasial</a>
        <a class='toc-link' href='#bab-3'>📊 Bab 3: Dimensi Multivariat</a>
        <a class='toc-link' href='#bab-4'>🌳 Bab 4: Dimensi Hierarkis</a>
        <a class='toc-link' href='#bab-5'>💡 Bab 5: Sintesis & Wawasan</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔍 Filter Penyorotan Wilayah")
    pulau_options = ["Semua Wilayah (38 Provinsi)"] + sorted(list(df['Pulau_Wilayah'].unique()))
    
    # Callback untuk reset filter secara instan dan andal
    def reset_filter_callback():
        st.session_state["pulau_selector"] = "Semua Wilayah (38 Provinsi)"

    selected_pulau = st.selectbox(
        "Fokus Analisis Pulau:",
        pulau_options,
        key="pulau_selector",
        help="Pilih pulau untuk menyorot provinsi terkait (38 provinsi tetap ditampilkan sebagai latar belakang)."
    )

    if selected_pulau != "Semua Wilayah (38 Provinsi)":
        st.button("🔄 Reset ke Semua Wilayah", on_click=reset_filter_callback, use_container_width=True)


# Injeksi Script Klien (assets/story.js): reveal-once, animasi filter, penanda bab, scroll-spy, progress bar
js_path = os.path.join("assets", "story.js")
if os.path.exists(js_path):
    with open(js_path, "r", encoding="utf-8") as f:
        story_js = f.read()
    st.components.v1.html(f"<script>{story_js}</script>", height=0)


# =========================================================
# HERO SECTION (DENGAN HOOK TEMUAN UTAMA & CTA)
# =========================================================
dki_ipm_hero = df.loc[df['Provinsi'] == 'DKI Jakarta', 'IPM_2025'].values[0]
papua_peg_ipm_hero = df.loc[df['Provinsi'] == 'Papua Pegunungan', 'IPM_2025'].values[0]
ipm_gap_hero = dki_ipm_hero - papua_peg_ipm_hero
pt_pdrb_hero = df.loc[df['Provinsi'] == 'Papua Tengah', 'PDRB_per_Kapita_HB_2025_ribu_Rp'].values[0] / 1000
pt_pov_hero = df.loc[df['Provinsi'] == 'Papua Tengah', 'Kemiskinan_September_2025_persen'].values[0]

st.markdown(f"""
<div class='story-hero reveal'>
    <div style='display:inline-block; background:rgba(255,255,255,0.15); padding:4px 14px; border-radius:20px; font-size:12px; font-weight:700; margin-bottom:12px; letter-spacing:0.5px;'>
        📊 DATA STORYTELLING • INDONESIA 2025
    </div>
    <h1>Indonesia 2025: Potret Pembangunan Sosial-Ekonomi</h1>
    <p>
        Menelusuri capaian pembangunan manusia, polarisasi spasial, keterkaitan multivariat, dan struktur ekonomi 38 provinsi di era Daerah Otonom Baru (DOB).
    </p>
    <div class='hero-hook'>
        <div class='hero-hook-title'>🔍 Temuan Kunci Utama:</div>
        <p class='hero-hook-desc'>
            Kesenjangan mutu hidup antardaerah masih terbentang lebar hingga <b>{ipm_gap_hero:.2f} poin IPM</b> antara DKI Jakarta ({dki_ipm_hero:.2f}) dan Papua Pegunungan ({papua_peg_ipm_hero:.2f}). 
            Di sisi lain, provinsi tambang seperti <b>Papua Tengah</b> menghadapi paradoks tajam: output PDRB per kapita tinggi (<b>Rp {pt_pdrb_hero:,.1f} juta</b>), namun persentase kemiskinannya tertinggi nasional (<b>{pt_pov_hero:.2f}%</b>).
        </p>
    </div>
    <div style='display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;'>
        <a href='#bab-1' class='btn-start-reading'>
            Mulai Membaca Cerita &nbsp;↓
        </a>
        <div style='font-size:12px; color:#93c5fd;'>
            ⏱️ Waktu baca: ~7 menit &nbsp;|&nbsp; 🏛️ Data Resmi BPS 2025 &nbsp;|&nbsp; 🗺️ Cakupan: 38 Provinsi Lengkap
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# BAB 1: LANSKAP MAKRO (OVERVIEW)
# =========================================================
chapter_opener(1, "LANSKAP MAKRO", "Menatap Indonesia 2025 dalam Angka",
    "Tahun 2025 menandai babak baru administrasi Indonesia setelah pemekaran resmi empat provinsi baru di Tanah Papua (Papua Barat Daya, Papua Selatan, Papua Tengah, dan Papua Pegunungan). Sebelum membedah detail kewilayahan, bagaimanakah potret kesejahteraan dan kinerja ekonomi Indonesia secara makro?")

overview = compute_national_overview_cards(df)

st.markdown("<div style='font-size:13px; font-weight:700; color:#475569; margin-bottom:12px;'>📊 Rata-Rata 38 Provinsi (Tidak Berbobot Penduduk):</div>", unsafe_allow_html=True)

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    st.markdown(f"""
    <div class='stis-metric-card reveal'>
        <div class='stis-card-title'>Indeks Pembangunan Manusia</div>
        <div class='stis-card-value'>{overview['ipm']['mean']:.2f} <span style='font-size:14px; font-weight:normal; color:#64748b;'>poin</span></div>
        <div class='stis-card-sub'>Tertinggi: <b>{overview['ipm']['max_prov']}</b> ({overview['ipm']['max_val']:.2f})<br>Terendah: <b>{overview['ipm']['min_prov']}</b> ({overview['ipm']['min_val']:.2f})</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
    <div class='stis-metric-card reveal'>
        <div class='stis-card-title'>Tingkat Kemiskinan</div>
        <div class='stis-card-value'>{overview['kemiskinan']['mean']:.2f}%</div>
        <div class='stis-card-sub'>Terendah: <b>{overview['kemiskinan']['min_prov']}</b> ({overview['kemiskinan']['min_val']:.2f}%)<br>Tertinggi: <b>{overview['kemiskinan']['max_prov']}</b> ({overview['kemiskinan']['max_val']:.2f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
    <div class='stis-metric-card reveal'>
        <div class='stis-card-title'>PDRB per Kapita (HB)</div>
        <div class='stis-card-value'>Rp {overview['pdrb_per_kapita']['mean_juta']:,.1f} <span style='font-size:14px; font-weight:normal; color:#64748b;'>jt</span></div>
        <div class='stis-card-sub'>Tertinggi: <b>{overview['pdrb_per_kapita']['max_prov']}</b> (Rp {overview['pdrb_per_kapita']['max_val_juta']:,.1f} jt)<br>Terendah: <b>{overview['pdrb_per_kapita']['min_prov']}</b> (Rp {overview['pdrb_per_kapita']['min_val_juta']:,.1f} jt)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
    <div class='stis-metric-card reveal'>
        <div class='stis-card-title'>Pengangguran Terbuka (TPT)</div>
        <div class='stis-card-value'>{overview['tpt']['mean']:.2f}%</div>
        <div class='stis-card-sub'>Terendah: <b>{overview['tpt']['min_prov']}</b> ({overview['tpt']['min_val']:.2f}%)<br>Tertinggi: <b>{overview['tpt']['max_prov']}</b> ({overview['tpt']['max_val']:.2f}%)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='font-size:12px; color:#64748b; margin-top:-6px; margin-bottom:14px;'>ℹ️ <i>Catatan Metodologis: Nilai rata-rata pada kartu di atas merupakan rata-rata 38 provinsi (tidak berbobot penduduk) guna membandingkan capaian antarentitas administratif pemerintahan daerah, bukan rata-rata agregat tertimbang populasi penduduk nasional.</i></div>", unsafe_allow_html=True)

# Expander Audit Kualitas Data Otomatis
with st.expander("🛡️ Audit Kualitas Data & Integritas Dataset (Validasi Otomatis)"):
    val_report = validate_dataset(df, geojson_data)
    if val_report['is_valid']:
        st.success("✅ **Dataset Valid:** Seluruh parameter integritas data lolos uji verifikasi otomatis.")
    else:
        st.warning("⚠️ **Terdapat Catatan Validasi:** Periksa detail pengujian di bawah.")
        
    for c in val_report['checks']:
        icon = "✅" if c['status'] else "❌"
        st.markdown(f"- **{icon} {c['name']}**: *Harapan*: `{c['expected']}` | *Aktual*: `{c['actual']}` — {c['message']}")

# Expander Rangkuman Statistik 9 Indikator
with st.expander("📊 Buka Tabel Rangkuman Statistik Deskriptif 9 Indikator Pembangunan"):
    stats_df = compute_summary_statistics(df)
    display_stats = stats_df[['Indikator', 'Satuan', 'Rata-rata', 'Median', 'Minimum', 'Provinsi Minimum', 'Maksimum', 'Provinsi Maksimum']].copy()
    display_stats['Rata-rata'] = display_stats['Rata-rata'].apply(lambda x: f"{x:,.2f}")
    display_stats['Median'] = display_stats['Median'].apply(lambda x: f"{x:,.2f}")
    display_stats['Minimum'] = display_stats['Minimum'].apply(lambda x: f"{x:,.2f}")
    display_stats['Maksimum'] = display_stats['Maksimum'].apply(lambda x: f"{x:,.2f}")
    render_table(display_stats, hide_index=True)


# JEMBATAN NARASI TRANSISI: BAB 1 -> BAB 2
st.markdown("""
<div class='story-bridge reveal'>
    <div class='story-bridge-tag'>🔄 Transisi Menuju Bab 2: Dari Angka Agregat ke Dimensi Spasial</div>
    💡 Angka rata-rata nasional kerap kali menyamarkan kenyataan di lapangan. 
    Indonesia bukanlah satu angka tunggal, melainkan hamparan 17.000 pulau dengan bentang tantangan yang sangat beragam. 
    <b>Di manakah sesungguhnya letak ketimpangan antarprovinsi di Nusantara? Mari kita amati secara spasial.</b>
</div>
""", unsafe_allow_html=True)


# =========================================================
# BAB 2: DIMENSI GEOSPASIAL (FRAGMENT INTERAKTIF)
# =========================================================
chapter_opener(2, "GEOSPATIAL", "Di Mana Posisi Setiap Provinsi?",
    "Peta tematik di bawah ini menyajikan distribusi geografis indikator pembangunan sosial-ekonomi di 38 provinsi. Gunakan dropdown untuk mengganti indikator yang ingin Anda telaah secara dinamis.")

@st.fragment
def render_geospatial_section(df, geojson_data, selected_pulau):
    """Bagian interaktif Bab 2 terisolasi dalam st.fragment agar perpindahan widget tidak merender ulang seluruh halaman."""
    geo_indicators = [
        'IPM_2025',
        'Kemiskinan_September_2025_persen',
        'PDRB_per_Kapita_HB_2025_ribu_Rp',
        'TPT_Agustus_2025_persen',
        'TPAK_Agustus_2025_persen',
        'TPK_Hotel_Berbintang_2025_persen',
        'TPK_Hotel_Nonbintang_2025_persen'
    ]

    c_map_ind, c_map_style = st.columns([3, 1])
    with c_map_ind:
        selected_ind = st.selectbox(
            "Pilih Indikator untuk Ditampilkan pada Peta:",
            geo_indicators,
            format_func=lambda x: INDICATOR_METADATA[x]['label'],
            key="geo_ind_select"
        )
    with c_map_style:
        map_layer = st.selectbox(
            "Gaya Lapisan Peta:",
            ["carto-positron", "white-bg", "open-street-map"],
            format_func=lambda x: "Peta Modern (Carto)" if x == "carto-positron" else "Peta Polos (White-bg)" if x == "white-bg" else "OpenStreetMap",
            key="map_style_select"
        )

    meta_ind = INDICATOR_METADATA[selected_ind]
    st.info(f"📌 **{meta_ind['label']}**: {meta_ind['desc']} *(Satuan: {meta_ind['unit']})*")

    # Render Peta dengan transisi halus
    fig_map = plot_choropleth_map(df, geojson_data, selected_ind, selected_pulau=selected_pulau, map_style=map_layer)
    chart_sig("map", selected_ind, map_layer, selected_pulau, fx="focus")
    render_plotly(fig_map, key="choropleth_map_chart")

    # Takeaway Dinamis Peta
    max_row = df.loc[df[selected_ind].idxmax()]
    min_row = df.loc[df[selected_ind].idxmin()]
    diff_val = max_row[selected_ind] - min_row[selected_ind]
    ratio_val = (max_row[selected_ind] / min_row[selected_ind]) if min_row[selected_ind] > 0 else 0
    st.markdown(f"""
    <div class='chart-takeaway'>
        💡 <b>Takeaway Spasial:</b> Disparitas wilayah tampak nyata pada indikator <b>{meta_ind['label']}</b>, 
        di mana capaian tertinggi diraih oleh <b>{max_row['Provinsi']}</b> ({max_row[selected_ind]:,.2f} {meta_ind['unit']}) 
        berbanding terendah di <b>{min_row['Provinsi']}</b> ({min_row[selected_ind]:,.2f} {meta_ind['unit']}), 
        menghasilkan rentang ketimpangan sebesar <b>{diff_val:,.2f} {meta_ind['unit']}</b> (rasio disparitas {ratio_val:.1f}x).
    </div>
    """, unsafe_allow_html=True)

    # Highlight Top 3 & Bottom 3
    filter_label_note = f"di Pulau {selected_pulau}" if selected_pulau != "Semua Wilayah (38 Provinsi)" else "Nasional (38 Provinsi)"
    df_context = df[df['Pulau_Wilayah'] == selected_pulau] if selected_pulau != "Semua Wilayah (38 Provinsi)" else df

    h_col1, h_col2 = st.columns(2)
    with h_col1:
        st.markdown(f"**🟢 3 Provinsi Tertinggi ({meta_ind['label']} - {filter_label_note}):**")
        top3 = df_context.sort_values(by=selected_ind, ascending=False).head(3)
        for _, r in top3.iterrows():
            st.write(f"- **{r['Provinsi']}** ({r['Pulau_Wilayah']}): `{r[selected_ind]:,.2f} {meta_ind['unit']}`")
            
    with h_col2:
        st.markdown(f"**🔴 3 Provinsi Terendah ({meta_ind['label']} - {filter_label_note}):**")
        bot3 = df_context.sort_values(by=selected_ind, ascending=True).head(3)
        for _, r in bot3.iterrows():
            st.write(f"- **{r['Provinsi']}** ({r['Pulau_Wilayah']}): `{r[selected_ind]:,.2f} {meta_ind['unit']}`")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚖️ Catatan Metodologis: Visualisasi Variabel Absolut vs Rasio")
    st.markdown("""
    Dalam kaidah kartografi data, **peta choropleth tidak boleh digunakan untuk menampilkan besaran agregat mutlak** 
    (seperti PDRB Total Riil atau Jumlah Penduduk Miskin) karena luas pulau akan mendistorsi persepsi mata (*area bias*). 
    Variabel absolut disajikan melalui **diagram batang komparatif terurut**:
    """)

    abs_option = st.radio(
        "Pilih Variabel Agregat Absolut:",
        ['PDRB_Total_ADHK_2025_miliar_Rp', 'Penduduk_Miskin_September_2025_ribu'],
        format_func=lambda x: INDICATOR_METADATA[x]['label'],
        horizontal=True,
        key="abs_radio_select"
    )

    fig_abs = plot_absolute_bar_comparison(df, col=abs_option, selected_pulau=selected_pulau)
    chart_sig("bar_abs", abs_option, selected_pulau, fx="grow")
    render_plotly(fig_abs, key="absolute_bar_chart")

    # Takeaway Dinamis Bar Chart
    jawa_sum = df[df['Pulau_Wilayah'] == 'Jawa'][abs_option].sum()
    total_abs = df[abs_option].sum()
    jawa_pct = (jawa_sum / total_abs) * 100
    top3_abs = df.sort_values(by=abs_option, ascending=False).head(3)['Provinsi'].tolist()
    st.markdown(f"""
    <div class='chart-takeaway'>
        💡 <b>Takeaway Komparatif:</b> Konsentrasi spasial agregat sangat mencolok: <b>Pulau Jawa mendominasi {jawa_pct:.1f}%</b> 
        dari total {INDICATOR_METADATA[abs_option]['label']} se-Indonesia, dengan tiga kontributor terbesar dipimpin oleh <b>{', '.join(top3_abs)}</b>.
    </div>
    """, unsafe_allow_html=True)

render_geospatial_section(df, geojson_data, selected_pulau)


# JEMBATAN NARASI TRANSISI: BAB 2 -> BAB 3
st.markdown("""
<div class='story-bridge reveal'>
    <div class='story-bridge-tag'>🔄 Transisi Menuju Bab 3: Menghubungkan Dimensi Sosial dan Ekonomi</div>
    💡 Peta tematik telah memperlihatkan polarisasi spasial yang tajam antara wilayah barat dan timur. 
    Namun, apakah tingginya output ekonomi selalu sejalan dengan tingginya mutu hidup manusia? 
    <b>Bagaimanakah indikator sosial-ekonomi saling berhubungan jika kita telaah secara multivariat?</b>
</div>
""", unsafe_allow_html=True)


# =========================================================
# BAB 3: DIMENSI MULTIVARIAT
# =========================================================
chapter_opener(3, "MULTIVARIATE", "Bagaimana Indikator Saling Berhubungan?",
    "Bagian ini membedah hubungan bivariat antarvariabel, matriks korelasi makro, mereduksi kompleksitas data melalui Principal Component Analysis (PCA), serta memetakan profil multidimensi dan tipologi wilayah.")

st.markdown("""
<div class='subnav reveal'>
    <a class='subnav-pill' href='#bab-3-1'><b>3.1</b> Hubungan Bivariat</a>
    <a class='subnav-pill' href='#bab-3-2'><b>3.2</b> Reduksi Dimensi (PCA)</a>
    <a class='subnav-pill' href='#bab-3-3'><b>3.3</b> Profil Multidimensi</a>
    <a class='subnav-pill' href='#bab-3-4'><b>3.4</b> Tipologi Wilayah</a>
</div>
""", unsafe_allow_html=True)

# 3.1 SCATTERPLOT BIVARIAT (FRAGMENT INTERAKTIF)
subchapter_header("3.1", "Analisis Hubungan Bivariat", "Scatterplot interaktif")

@st.fragment
def render_multivariate_scatter_section(df, selected_pulau):
    st.markdown("Pilih dua variabel indikator untuk memeriksa pola sebaran data, keeratan korelasi linier, dan garis tren OLS:")

    all_numeric = get_numeric_indicators()
    c_x, c_y, c_opt = st.columns([2, 2, 1])
    with c_x:
        x_var = st.selectbox(
            "Variabel Sumbu X:",
            all_numeric,
            index=0, # IPM
            format_func=lambda x: INDICATOR_METADATA[x]['label'],
            key="scatter_x_select"
        )
    with c_y:
        y_var = st.selectbox(
            "Variabel Sumbu Y:",
            all_numeric,
            index=2, # Kemiskinan %
            format_func=lambda x: INDICATOR_METADATA[x]['label'],
            key="scatter_y_select"
        )
    with c_opt:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        show_trend = st.checkbox("Garis Tren Linear", value=True, key="scatter_trend_cb")

    fig_scatter = plot_bivariate_scatter(df, x_var, y_var, selected_pulau=selected_pulau, add_trendline=show_trend)
    chart_sig("scatter", x_var, y_var, show_trend, selected_pulau, fx="morph")
    render_plotly(fig_scatter, key="bivariate_scatter_chart")

    if x_var != y_var:
        corr_val = df[x_var].corr(df[y_var])
        r2_val = corr_val ** 2
        strength = "sangat kuat" if abs(corr_val) > 0.7 else "kuat" if abs(corr_val) > 0.5 else "sedang" if abs(corr_val) > 0.3 else "lemah"
        arah = "positif (searah)" if corr_val > 0 else "negatif (berlawanan)"
        
        st.markdown(f"""
        <div class='chart-takeaway'>
            💡 <b>Takeaway Hubungan Bivariat:</b> Terdapat korelasi linear <b>{arah} yang {strength} (r = {corr_val:+.3f}, R² = {r2_val:.3f})</b> 
            antara {INDICATOR_METADATA[x_var]['label']} dan {INDICATOR_METADATA[y_var]['label']}. 
            Variasi pada sumbu X mengasosiasikan sekitar <b>{r2_val * 100:.1f}%</b> variasi pada sumbu Y. 
            <i>Ingat: Korelasi empiris ini menunjukkan derajat asosiasi statistik linier dan bukan hubungan sebab-akibat (kausalitas).</i>
        </div>
        """, unsafe_allow_html=True)

render_multivariate_scatter_section(df, selected_pulau)

# Matriks Korelasi Lengkap 9 Indikator
with st.expander("🔥 Tampilkan Matriks Korelasi Pearson Lengkap (Heatmap 9 Indikator)"):
    fig_heat = plot_correlation_heatmap(df)
    render_plotly(fig_heat, key="corr_heatmap_chart")
    st.markdown("""
    <div class='chart-takeaway'>
        💡 <b>Takeaway Matriks Korelasi:</b> Hubungan negatif paling kuat teramati antara <b>IPM dan Kemiskinan (%)</b>, 
        sedangkan korelasi positif paling solid terlihat antara <b>IPM dan PDRB per kapita</b> serta akomodasi hotel pariwisata. 
        TPAK dan TPT memperlihatkan keterikatan linear yang relatif rendah terhadap output ekonomi makro.
    </div>
    """, unsafe_allow_html=True)

# Transisi Sub-bab: 3.1 -> 3.2
st.markdown("""
<div class='subchapter-bridge reveal'>
    🔍 <b>Transisi Sub-bab (3.1 ke 3.2):</b> Memeriksa korelasi dua-per-dua membuka tabir hubungan awal, 
    namun bagaimanakah jika kita merangkum keseluruhan 9 indikator secara simultan? Mari kita telaah melalui reduksi dimensi Principal Component Analysis (PCA).
</div>
""", unsafe_allow_html=True)

# 3.2 REDUKSI DIMENSI (PCA)
subchapter_header("3.2", "Reduksi Dimensi Data", "Principal Component Analysis (PCA)")
st.markdown("""
Ketika dihadapkan pada 9 indikator sekaligus, sulit melihat posisi komprehensif suatu provinsi secara kasat mata. 
**PCA** merangkum kesembilan dimensi tersebut menjadi 2 Komponen Utama (PC1 dan PC2) setelah seluruh variabel distandarisasi 
menggunakan *Z-Score Standardization* (`StandardScaler`).
""")

pca_results = run_cached_pca(df)

top_pc1_pos = pca_results['top_pc1_pos']
top_pc1_neg = pca_results['top_pc1_neg']
top3_pc2 = pca_results['top3_pc2']

pc1_axis_label = f"Kesejahteraan ({top_pc1_pos['Indikator']}) vs Deprivasi ({top_pc1_neg['Indikator']})"
pc2_axis_label = f"Skala Aglomerasi & Partisipasi Kerja ({top3_pc2.iloc[0]['Indikator']}, {top3_pc2.iloc[1]['Indikator']})"

v_col1, v_col2, v_col3 = st.columns(3)
with v_col1:
    st.metric(
        "Varians PC1",
        f"{pca_results['var_pc1']:.1f}%",
        help=f"Dominan: {top_pc1_pos['Indikator']} (+{top_pc1_pos['Loading_PC1']:.2f}) vs {top_pc1_neg['Indikator']} ({top_pc1_neg['Loading_PC1']:.2f})"
    )
with v_col2:
    st.metric(
        "Varians PC2",
        f"{pca_results['var_pc2']:.1f}%",
        help=f"Dominan: {top3_pc2.iloc[0]['Indikator']} (+{top3_pc2.iloc[0]['Loading_PC2']:.2f}), {top3_pc2.iloc[1]['Indikator']} (+{top3_pc2.iloc[1]['Loading_PC2']:.2f})"
    )
with v_col3:
    st.metric(
        "Total Varians (2 PC)",
        f"{pca_results['total_var']:.1f}%",
        help=f"Dua komponen utama pertama berhasil merangkum {pca_results['total_var']:.1f}% dari total variasi 9 indikator pembangunan."
    )

fig_biplot = plot_pca_biplot(
    pca_results['pca_df'],
    pca_results['loadings_df'],
    pca_results['var_pc1'],
    pca_results['var_pc2'],
    selected_pulau=selected_pulau,
    pc1_label=pc1_axis_label,
    pc2_label=pc2_axis_label
)
chart_sig("pca", selected_pulau, fx="morph")
render_plotly(fig_biplot, key="pca_biplot_chart")

st.markdown(f"""
<div class='chart-takeaway'>
    💡 <b>Takeaway PCA Biplot:</b> Dua komponen utama merangkum <b>{pca_results['total_var']:.1f}%</b> variasi data 38 provinsi. 
    <b>PC1 ({pca_results['var_pc1']:.1f}%)</b> mencerminkan polarisasi Kesejahteraan vs Deprivasi (memisahkan DKI/Bali di kanan vs Papua Pegunungan di kiri), 
    sedangkan <b>PC2 ({pca_results['var_pc2']:.1f}%)</b> menangkap Skala Aglomerasi Penduduk Miskin dan Partisipasi Kerja Agregat.
</div>
""", unsafe_allow_html=True)

col_scree, col_interp = st.columns([1, 1])
with col_scree:
    fig_scree = plot_pca_variance_bars(pca_results['pca_model'], pca_results['feature_cols'])
    render_plotly(fig_scree, key="scree_plot_chart")
with col_interp:
    load_pkin = pca_results['loadings_df'].loc['Penduduk_Miskin_September_2025_ribu', 'Loading_PC2']
    load_tpak = pca_results['loadings_df'].loc['TPAK_Agustus_2025_persen', 'Loading_PC2']
    load_pdrb = pca_results['loadings_df'].loc['PDRB_Total_ADHK_2025_miliar_Rp', 'Loading_PC2']
    st.markdown(f"""
    **Interpretasi Makna Sumbu PCA (Diturunkan Dinamis dari Matriks Loading):**
    - **Sumbu Horizontal (PC1 — {pca_results['var_pc1']:.1f}% Varians)**: *Dimensi Kesejahteraan vs Deprivasi*.
      - Loading positif tertinggi: **{top_pc1_pos['Indikator']} (+{top_pc1_pos['Loading_PC1']:.2f})**, PDRB per kapita, dan akomodasi pariwisata.
      - Loading negatif terkuat: **{top_pc1_neg['Indikator']} ({top_pc1_neg['Loading_PC1']:.2f})**.
    - **Sumbu Vertikal (PC2 — {pca_results['var_pc2']:.1f}% Varians)**: *Dimensi Skala Aglomerasi & Partisipasi Kerja*.
      - Loading PC2 didominasi oleh **Jumlah Penduduk Miskin (+{load_pkin:.2f})**, **TPAK (+{load_tpak:.2f})**, dan **PDRB Total ADHK (+{load_pdrb:.2f})**.
    """)

# Transisi Sub-bab: 3.2 -> 3.3
st.markdown("""
<div class='subchapter-bridge reveal'>
    📊 <b>Transisi Sub-bab (3.2 ke 3.3):</b> PCA telah mereduksi 9 indikator ke bidang koordinat 2 dimensi. 
    Selanjutnya, mari telusuri profil spesifik setiap provinsi melintasi masing-masing sumbu indikator secara langsung melalui koordinat sejajar (*Parallel Coordinates*).
</div>
""", unsafe_allow_html=True)

# 3.3 PARALLEL COORDINATES
subchapter_header("3.3", "Profil Multidimensi Provinsi", "Parallel Coordinates")
st.markdown("""
Melalui grafik koordinat sejajar ini, Anda dapat melacak garis profil setiap provinsi melintasi berbagai indikator sekaligus.
*Tips Interaksi: Tarik dan geser mouse (*brushing*) pada sumbu mana pun untuk memfilter kelompok provinsi tertentu.*
""")

c_par1, c_par2 = st.columns([3, 1])
with c_par2:
    highlight_prov_par = st.multiselect(
        "Periksa Detail Provinsi:",
        options=sorted(df['Provinsi'].tolist()),
        default=['DKI Jakarta', 'DI Yogyakarta', 'Bali', 'Papua Tengah'],
        help="Pilih satu atau beberapa provinsi untuk melihat tabel profil indikator terfilternya di bawah."
    )

with c_par1:
    fig_par = plot_parallel_coordinates(df)
    render_plotly(fig_par, key="parallel_coordinates_chart")

if highlight_prov_par:
    st.markdown(f"**📋 Ringkasan Profil Provinsi Terpilih ({len(highlight_prov_par)} Provinsi):**")
    par_subset = df[df['Provinsi'].isin(highlight_prov_par)][
        ['Provinsi', 'Pulau_Wilayah', 'IPM_2025', 'Kemiskinan_September_2025_persen', 'PDRB_per_Kapita_HB_2025_ribu_Rp', 'TPT_Agustus_2025_persen', 'TPAK_Agustus_2025_persen']
    ].copy()
    chart_sig("par_table", ",".join(sorted(highlight_prov_par)), fx="focus")
    render_table(par_subset, hide_index=True)

st.markdown("""
<div class='chart-takeaway'>
    💡 <b>Takeaway Multidimensi:</b> Profil garis parallel coordinates menyingkap anomali terputus (*decoupling*): 
    provinsi dengan TPAK sangat tinggi (seperti Papua Pegunungan) kerap kali memiliki capaian IPM dan PDRB per kapita di rentang paling bawah, 
    sementara DKI Jakarta dan Bali memperlihatkan garis datar stabil di kuadran kesejahteraan atas.
</div>
""", unsafe_allow_html=True)

# Transisi Sub-bab: 3.3 -> 3.4
st.markdown("""
<div class='subchapter-bridge reveal'>
    🏷️ <b>Transisi Sub-bab (3.3 ke 3.4):</b> Pola bentangan garis antardaerah tersebut secara empiris menunjukkan kemiripan kelompok. 
    Bagaimanakah algoritma *K-Means* merangkum 38 provinsi ke dalam 4 tipologi pembangunan yang aplikatif bagi perencanaan kebijakan?
</div>
""", unsafe_allow_html=True)

# 3.4 TIPOLOGI WILAYAH (CLUSTERING)
subchapter_header("3.4", "Tipologi Wilayah Pembangunan", "K-Means Clustering")
st.markdown("""
Dengan algoritma *K-Means* ($k=4$) berbasis fitur terstandarisasi, ke-38 provinsi di Indonesia secara empiris 
terkelompokkan ke dalam **empat tipologi sosial-ekonomi** yang memiliki karakteristik profil unik dan saling melengkapi:
""")

cluster_df, cluster_labels, cluster_profile = run_cached_clustering(df)

fig_cl = plot_cluster_scatter(cluster_df, selected_pulau=selected_pulau)
chart_sig("cluster", selected_pulau, fx="morph")
render_plotly(fig_cl, key="cluster_scatter_chart")

st.markdown("""
<div class='chart-takeaway'>
    💡 <b>Takeaway Tipologi:</b> Algoritma K-Means mengelompokkan 38 provinsi ke dalam 4 tipologi: 
    <b>Sentra Ekonomi Maju</b> (DKI, Bali, Kep. Riau), <b>Berkembang Sedang</b> (mayoritas Jawa & Sumatera), 
    <b>Transisi Ketenagakerjaan</b> (Jabar, Banten), dan <b>Tantangan Struktural DOB Papua</b> (Papua Tengah, Pegunungan, Papua Barat).
</div>
""", unsafe_allow_html=True)

with st.expander("📋 Tampilkan Profil Centroid & Bukti Pemilihan k=4 (Elbow & Silhouette)"):
    st.markdown("#### 1. Rata-Rata Karakteristik Setiap Klaster:")
    display_profile = cluster_profile.copy()
    display_profile.index = [cluster_labels[i] for i in display_profile.index]
    render_table(display_profile.style.format("{:,.2f}"), hide_index=False)

    st.markdown("#### 2. Justifikasi Penentuan Jumlah Klaster ($k=4$):")
    st.markdown("""
    Pemilihan $k=4$ didasarkan pada kombinasi metode empiris kuantitatif dan interpretasi substantif:
    - **Metode Elbow (Inersia)**: Penurunan inersia melandai tajam setelah $k=4$, menandakan titik infleksi optimal (*elbow point*).
    - **Silhouette Score**: Memberikan koefisien pemisahan yang seimbang tanpa memecah klaster menjadi singleton.
    - **Relevansi Substantif**: Menghasilkan 4 tipologi kebijakan yang sangat aplikatif bagi perencanaan pembangunan wilayah.
    """)
    val_metrics = compute_cluster_validation_metrics(df)
    render_table(val_metrics, hide_index=True)


# JEMBATAN NARASI TRANSISI: BAB 3 -> BAB 4
st.markdown("""
<div class='story-bridge reveal'>
    <div class='story-bridge-tag'>🔄 Transisi Menuju Bab 4: Dari Multivariat ke Struktur Berjenjang</div>
    💡 Kita telah melihat bagaimana provinsi berkelompok berdasarkan karakteristik multidimensinya. 
    Namun dalam tata kelola kenegaraan, wilayah terikat dalam tatanan spasial hierarkis nusantara. 
    <b>Bagaimanakah kontribusi dan mutu pembangunan jika didekomposisi secara berjenjang dari Pusat, Pulau, hingga Provinsi?</b>
</div>
""", unsafe_allow_html=True)


# =========================================================
# BAB 4: DIMENSI HIERARKIS (FRAGMENT INTERAKTIF)
# =========================================================
chapter_opener(4, "HIERARCHICAL", "Struktur Kewilayahan Nusantara Secara Berjenjang",
    "Visualisasi hierarkis mendekomposisi wilayah Indonesia ke dalam struktur tiga tingkat: <b>Indonesia (Nasional) → Pulau / Wilayah → Provinsi</b>.")

@st.fragment
def render_hierarchical_section(df):
    """Bagian interaktif Bab 4 terisolasi dalam st.fragment."""
    c_tree_type, c_tree_size = st.columns([1, 1])
    with c_tree_type:
        hier_type = st.radio("Pilih Bentuk Visualisasi:", ["Treemap (Kotak Bersarang)", "Sunburst (Cincin Konsentris)"], horizontal=True, key="hier_type_radio")
    with c_tree_size:
        hier_size = st.selectbox(
            "Indikator Penentu Ukuran Sektor (Variabel Agregat Aditif):",
            ['PDRB_Total_ADHK_2025_miliar_Rp', 'Penduduk_Miskin_September_2025_ribu'],
            format_func=lambda x: INDICATOR_METADATA[x]['label'],
            help="Pilihan ukuran dibatasi pada variabel agregat aditif yang valid dijumlahkan antarlevel hierarki.",
            key="hier_size_select"
        )

    if "Treemap" in hier_type:
        fig_hier = plot_treemap(df, size_col=hier_size, color_col='IPM_2025')
    else:
        fig_hier = plot_sunburst(df, size_col=hier_size, color_col='IPM_2025')

    chart_sig("hier", hier_type, hier_size, fx="cascade")
    render_plotly(fig_hier, key="hierarchical_chart")

    # Takeaway Dinamis Hierarki
    island_agg = df.groupby('Hierarki_Level_2')[hier_size].sum()
    top_island = island_agg.idxmax()
    top_island_val = island_agg.max()
    total_agg = island_agg.sum()
    top_pct = (top_island_val / total_agg) * 100
    st.markdown(f"""
    <div class='chart-takeaway'>
        💡 <b>Takeaway Dekomposisi Hierarki:</b> Pada struktur bertingkat 3-level, wilayah <b>{top_island}</b> 
        menguasai pangsa terbesar yaitu <b>{top_pct:.1f}%</b> dari total agregat nasional {INDICATOR_METADATA[hier_size]['label']}, 
        menunjukkan tingginya sentralitas spasial yang membutuhkan kebijakan afirmatif pemerataan antarwilayah.
    </div>
    """, unsafe_allow_html=True)

render_hierarchical_section(df)


# JEMBATAN NARASI TRANSISI: BAB 4 -> BAB 5
st.markdown("""
<div class='story-bridge reveal'>
    <div class='story-bridge-tag'>🔄 Transisi Menuju Bab 5: Menarik Benang Merah Sintesis Kebijakan</div>
    💡 Dari potret makro, peta geospasial, keterkaitan multivariat, hingga dekomposisi struktur hierarki, 
    seluruh kepingan data empiris 2025 telah tersusun utuh. 
    <b>Pelajaran dan implikasi kebijakan strategis apa yang dapat kita rumuskan bagi masa depan pembangunan Indonesia?</b>
</div>
""", unsafe_allow_html=True)


# =========================================================
# BAB 5: SINTESIS ANALITIK & PENUTUP
# =========================================================
chapter_opener(5, "SINTESIS & INSIGHT", "Apa yang Dapat Kita Pelajari?",
    "Sintesis temuan analitis berbasis data empiris Badan Pusat Statistik (BPS) 2025 tanpa klaim kausalitas spekulatif.")

# Data dinamis untuk narasi Bab 5
dki_ipm = df.loc[df['Provinsi'] == 'DKI Jakarta', 'IPM_2025'].values[0]
jawa_bali_min_ipm = df[df['Pulau_Wilayah'].isin(['Jawa', 'Bali & Nusa Tenggara']) & (~df['Provinsi'].isin(['Nusa Tenggara Barat', 'Nusa Tenggara Timur']))]['IPM_2025'].min()
papua_peg_ipm = df.loc[df['Provinsi'] == 'Papua Pegunungan', 'IPM_2025'].values[0]
papua_tgh_ipm = df.loc[df['Provinsi'] == 'Papua Tengah', 'IPM_2025'].values[0]
ntt_ipm = df.loc[df['Provinsi'] == 'Nusa Tenggara Timur', 'IPM_2025'].values[0]

pt_pdrb_jt = df.loc[df['Provinsi'] == 'Papua Tengah', 'PDRB_per_Kapita_HB_2025_ribu_Rp'].values[0] / 1000
pt_pov = df.loc[df['Provinsi'] == 'Papua Tengah', 'Kemiskinan_September_2025_persen'].values[0]
pb_pdrb_jt = df.loc[df['Provinsi'] == 'Papua Barat', 'PDRB_per_Kapita_HB_2025_ribu_Rp'].values[0] / 1000
pb_pov = df.loc[df['Provinsi'] == 'Papua Barat', 'Kemiskinan_September_2025_persen'].values[0]

pp_tpak = df.loc[df['Provinsi'] == 'Papua Pegunungan', 'TPAK_Agustus_2025_persen'].values[0]
pp_tpt = df.loc[df['Provinsi'] == 'Papua Pegunungan', 'TPT_Agustus_2025_persen'].values[0]
bali_tpak = df.loc[df['Provinsi'] == 'Bali', 'TPAK_Agustus_2025_persen'].values[0]
bali_tpt = df.loc[df['Provinsi'] == 'Bali', 'TPT_Agustus_2025_persen'].values[0]
bali_pov = df.loc[df['Provinsi'] == 'Bali', 'Kemiskinan_September_2025_persen'].values[0]
bali_hotel = df.loc[df['Provinsi'] == 'Bali', 'TPK_Hotel_Berbintang_2025_persen'].values[0]
ntb_tpak = df.loc[df['Provinsi'] == 'Nusa Tenggara Barat', 'TPAK_Agustus_2025_persen'].values[0]
ntb_tpt = df.loc[df['Provinsi'] == 'Nusa Tenggara Barat', 'TPT_Agustus_2025_persen'].values[0]

jabar_tpt = df.loc[df['Provinsi'] == 'Jawa Barat', 'TPT_Agustus_2025_persen'].values[0]
banten_tpt = df.loc[df['Provinsi'] == 'Banten', 'TPT_Agustus_2025_persen'].values[0]
dki_tpt = df.loc[df['Provinsi'] == 'DKI Jakarta', 'TPT_Agustus_2025_persen'].values[0]

diy_ipm = df.loc[df['Provinsi'] == 'DI Yogyakarta', 'IPM_2025'].values[0]
diy_pov = df.loc[df['Provinsi'] == 'DI Yogyakarta', 'Kemiskinan_September_2025_persen'].values[0]
nat_pov_mean = df['Kemiskinan_September_2025_persen'].mean()

# 5 Kartu Insight Mendalam dengan angka dinamis & bahasa asosiasi
st.markdown(f"""
<div class='insight-card reveal'>
    <h4>1. Polarisasi Spasial Barat vs Timur yang Masih Membatu</h4>
    <p>
        Data menunjukkan bahwa disparitas spasial antara Kawasan Barat Indonesia (KBI) dan Kawasan Timur Indonesia (KTI) masih menjadi tantangan struktural utama. 
        Seluruh provinsi di Pulau Jawa dan Bali mencatatkan <b>IPM di atas {jawa_bali_min_ipm:.2f} poin</b>, dipimpin oleh DKI Jakarta ({dki_ipm:.2f}). 
        Sebaliknya, wilayah Papua Pegunungan ({papua_peg_ipm:.2f}), Papua Tengah ({papua_tgh_ipm:.2f}), dan Nusa Tenggara Timur ({ntt_ipm:.2f}) masih menghadapi tantangan akses layanan dasar pendidikan dan kesehatan, 
        dengan persentase kemiskinan yang masih berada pada kisaran 17% hingga 29%.
    </p>
</div>

<div class='insight-card reveal'>
    <h4>2. Paradoks Pertambangan: Kecenderungan Pola "Enclave Economy"</h4>
    <p>
        Pemeriksaan terhadap sebaran bivariat dan hierarki memperlihatkan anomali mencolok pada provinsi berbasis ekstraktif sumber daya alam. 
        <b>Papua Tengah</b> mencatatkan PDRB per kapita di atas rata-rata 38 provinsi (<b>Rp {pt_pdrb_jt:,.2f} juta/tahun</b>), namun persentase kemiskinannya merupakan yang tertinggi nasional (<b>{pt_pov:.2f}%</b>). 
        Pola asosiasi serupa teramati di <b>Papua Barat</b> (PDRB per kapita Rp {pb_pdrb_jt:,.2f} juta vs kemiskinan {pb_pov:.2f}%). 
        Data ini sejalan dengan karakteristik industri padat modal (<i>capital-intensive</i>) di mana output bernilai tinggi terakumulasi secara agregat, namun memiliki keterkaitan ekonomi lokal dan daya serap tenaga kerja yang terbatas.
    </p>
</div>

<div class='insight-card reveal'>
    <h4>3. Dinamika Ketenagakerjaan: Sektor Agraris/Informal vs Pasar Tenaga Kerja Urban</h4>
    <p>
        Terdapat perbedaan struktur ketenagakerjaan yang nyata antara daerah agraris dan pusat perkotaan:
        <br>• <b>Papua Pegunungan</b> mencatat Tingkat Partisipasi Angkatan Kerja (TPAK) tertinggi di Indonesia sebesar <b>{pp_tpak:.2f}%</b> dengan Tingkat Pengangguran Terbuka (TPT) sebesar <b>{pp_tpt:.2f}%</b>, mencerminkan tingginya keterlibatan masyarakat pada aktivitas subsisten dan pertanian nonformal.
        <br>• <b>Bali</b> dan <b>Nusa Tenggara Barat</b> juga memperlihatkan partisipasi kerja tinggi (TPAK Bali {bali_tpak:.2f}%, NTB {ntb_tpak:.2f}%) dengan pengangguran relatif rendah (TPT Bali {bali_tpt:.2f}%, NTB {ntb_tpt:.2f}%), ditopang oleh geliat ekosistem pariwisata, pertanian, dan jasa.
        <br>• Sebaliknya di provinsi industri metropolitan seperti Jawa Barat (TPT <b>{jabar_tpt:.2f}%</b>), Banten (<b>{banten_tpt:.2f}%</b>), dan DKI Jakarta (<b>{dki_tpt:.2f}%</b>), angka pengangguran terbuka lebih tinggi seiring tingginya proporsi pencari kerja di pasar tenaga kerja formal yang membutuhkan penyesuaian kualifikasi (<i>job matching</i>).
    </p>
</div>

<div class='insight-card reveal'>
    <h4>4. Dua Kasus Unik: DI Yogyakarta dan Bali</h4>
    <p>
        • <b>DI Yogyakarta</b>: Meraih IPM tertinggi kedua di Indonesia (<b>{diy_ipm:.2f}</b>) berkat ekosistem pendidikan dan kesehatan yang sangat mapan. Namun, persentase kemiskinannya tercatat <b>{diy_pov:.2f}%</b>, yang merupakan <i>tertinggi di Pulau Jawa</i>, meskipun berada sedikit di bawah rata-rata unweighted 38 provinsi ({nat_pov_mean:.2f}%). Hal ini berkaitan erat dengan tingginya penetapan Garis Kemiskinan (GK) akibat standar keranjang konsumsi makanan dan nonmakanan di DIY.<br>
        • <b>Bali</b>: Menunjukkan performa pemulihan ekonomi pariwisata yang sangat solid, dengan TPT terendah nasional (<b>{bali_tpt:.2f}%</b>), kemiskinan terendah nasional (<b>{bali_pov:.2f}%</b>), serta tingkat penghunian kamar (TPK) hotel berbintang tertinggi (<b>{bali_hotel:.0f}%</b>).
    </p>
</div>

<div class='insight-card reveal'>
    <h4>5. Implikasi Kebijakan: Perlunya Kebijakan Terarah (*Targeted Policy*)</h4>
    <p>
        Perbedaan kondisi lintas wilayah mengindikasikan bahwa intervensi pembangunan tidak dapat diseragamkan (<i>one-size-fits-all</i>). 
        Untuk wilayah Kawasan Timur Indonesia dan Daerah Otonom Baru (DOB) Papua, fokus mendesak bertumpu pada penyediaan konektivitas logistik dasar, sarana sanitasi, puskesmas, serta pemerataan guru dan sekolah. 
        Sementara di kawasan metropolitan barat, prioritas bergeser pada peningkatan produktivitas industri, penciptaan lapangan kerja formal berkualitas tinggi, serta penguatan keterampilan digital tenaga kerja muda.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# BAGIAN METODOLOGI & KETERBATASAN DATA
# =========================================================
with st.expander("📚 Metodologi Analisis, Keterbatasan Data, & Definisi Indikator"):
    st.markdown("""
    #### 1. Pendekatan Analisis & Keterbatasan
    - **Sifat Data (Cross-Sectional)**: Seluruh analisis menggunakan data *cross-section* tahun 2025. Data mencerminkan potret kondisi pada satu titik waktu dan tidak menggambarkan tren longitudinal dinamis sebelum tahun 2025.
    - **Ukuran Sampel ($n = 38$)**: Analisis dibatasi pada 38 provinsi di Indonesia sebagai entitas makro administratif. Ukuran sampel yang terbatas membatasi generalisasi estimasi regresi parametrik tingkat tinggi.
    - **Implikasi Daerah Otonom Baru (DOB) Papua**: Pemekaran 4 provinsi baru di Papua (Papua Selatan, Papua Tengah, Papua Pegunungan, dan Papua Barat Daya berdasarkan UU No. 14, 15, 16, dan 29 Tahun 2022) menandai pencatatan statistik mandiri awal. Sebagian indikator berada pada tahap konsolidasi kelembagaan daerah baru.
    - **Agregasi Unweighted vs Weighted**: Nilai rata-rata pada kartu metrik makro dihitung secara *unweighted* (rata-rata aritmetika 38 provinsi) untuk mengamati disparitas performa pemerintahan antardaerah otonom, berbeda dari rata-rata agregat tertimbang populasi nasional.

    #### 2. Sumber Data & Lisensi Batas Spasial
    - **Dataset Sosial-Ekonomi**: Badan Pusat Statistik (BPS) Republik Indonesia, publikasi dan rilis resmi tahun 2025.
    - **Geometri Batas Wilayah**: Peta batas administrasi 38 provinsi bersumber dari repositori terbuka GeoJSON Indonesia, diselaraskan nama kode wilayahnya untuk menjamin pencocokan join 100% presisi.

    #### 3. Definisi Operasional 9 Indikator BPS
    """)
    meta_table_rows = []
    for k, v in INDICATOR_METADATA.items():
        meta_table_rows.append({
            'Kode Indikator': k,
            'Nama Indikator': v['label'],
            'Satuan': v['unit'],
            'Arah Kualitas': 'Makin Tinggi Makin Baik' if v['direction'] == 'higher_better' else 'Makin Rendah Makin Baik',
            'Definisi Konseptual': v['desc']
        })
    render_table(pd.DataFrame(meta_table_rows), hide_index=True)


# =========================================================
# FOOTER RESMI & SUMBER DATA
# =========================================================
st.markdown("<div class='story-divider'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; padding: 28px 0; color: #64748b; font-size: 13.5px; line-height: 1.8;'>
    <b>Indonesia 2025: Potret Pembangunan Sosial-Ekonomi</b><br>
    Proyek Ujian Akhir Semester (UAS) Mata Kuliah <b>Visualisasi Data dan Informasi</b><br>
    <b>Politeknik Statistika STIS</b> • Tahun Akademik 2025/2026<br>
    <div style='margin-top:8px; font-size:12px; color:#94a3b8;'>
        Sumber Data: <b>Badan Pusat Statistik (BPS) Republik Indonesia (2025)</b> &nbsp;|&nbsp; 
        Batas Wilayah: <b>GeoJSON Batas 38 Provinsi Indonesia</b>
    </div>
</div>
""", unsafe_allow_html=True)
