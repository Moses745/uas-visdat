"""
utils/preprocessing.py
Modul untuk memuat, membersihkan, menstandarisasi, dan memvalidasi dataset BPS serta GeoJSON.
Proyek UAS Visualisasi Data dan Informasi - Politeknik Statistika STIS
"""

import os
import json
import pandas as pd
import numpy as np

# Metadata indikator untuk visualisasi, label, satuan, dan interpretasi
INDICATOR_METADATA = {
    'IPM_2025': {
        'label': 'Indeks Pembangunan Manusia (IPM)',
        'unit': 'Poin',
        'format': ':.2f',
        'direction': 'higher_better',
        'cmap': 'Viridis',
        'desc': 'Mengukur capaian pembangunan manusia berbasis kesehatan, pendidikan, dan standar hidup layak.'
    },
    'PDRB_per_Kapita_HB_2025_ribu_Rp': {
        'label': 'PDRB per Kapita (Harga Berlaku)',
        'unit': 'Ribu Rp/Tahun',
        'format': ':,d',
        'direction': 'higher_better',
        'cmap': 'Plasma',
        'desc': 'Produk Domestik Regional Bruto per kapita atas dasar harga berlaku dalam ribuan rupiah.'
    },
    'Kemiskinan_September_2025_persen': {
        'label': 'Tingkat Kemiskinan (%)',
        'unit': '%',
        'format': ':.2f',
        'direction': 'lower_better',
        'cmap': 'YlOrRd',
        'desc': 'Persentase penduduk yang berada di bawah garis kemiskinan pada September 2025.'
    },
    'Penduduk_Miskin_September_2025_ribu': {
        'label': 'Jumlah Penduduk Miskin',
        'unit': 'Ribu Jiwa',
        'format': ':,.1f',
        'direction': 'lower_better',
        'cmap': 'OrRd',
        'desc': 'Jumlah mutlak penduduk miskin dalam ribuan jiwa.'
    },
    'TPT_Agustus_2025_persen': {
        'label': 'Tingkat Pengangguran Terbuka (TPT)',
        'unit': '%',
        'format': ':.2f',
        'direction': 'lower_better',
        'cmap': 'Reds',
        'desc': 'Persentase angkatan kerja yang tidak bekerja dan sedang mencari pekerjaan.'
    },
    'TPAK_Agustus_2025_persen': {
        'label': 'Tingkat Partisipasi Angkatan Kerja (TPAK)',
        'unit': '%',
        'format': ':.2f',
        'direction': 'higher_better',
        'cmap': 'Teal',
        'desc': 'Persentase penduduk usia kerja yang aktif secara ekonomi dalam pasar kerja.'
    },
    'TPK_Hotel_Berbintang_2025_persen': {
        'label': 'TPK Hotel Berbintang',
        'unit': '%',
        'format': ':.1f',
        'direction': 'higher_better',
        'cmap': 'Blues',
        'desc': 'Tingkat Penghunian Kamar pada hotel klasifikasi bintang sebagai proksi aktivitas pariwisata & bisnis.'
    },
    'TPK_Hotel_Nonbintang_2025_persen': {
        'label': 'TPK Hotel Nonbintang',
        'unit': '%',
        'format': ':.1f',
        'direction': 'higher_better',
        'cmap': 'Purples',
        'desc': 'Tingkat Penghunian Kamar pada hotel klasifikasi nonbintang.'
    },
    'PDRB_Total_ADHK_2025_miliar_Rp': {
        'label': 'PDRB Total Riil (ADHK)',
        'unit': 'Miliar Rp',
        'format': ':,.1f',
        'direction': 'higher_better',
        'cmap': 'Viridis',
        'desc': 'Total output ekonomi riil atas dasar harga konstan dalam satuan miliar rupiah.'
    }
}

# Mapping nama provinsi aman antara CSV dan GeoJSON
PROVINCE_NAME_MAPPING = {
    'DI Yogyakarta': 'Daerah Istimewa Yogyakarta',
    'D.I. Yogyakarta': 'Daerah Istimewa Yogyakarta',
    'DIY': 'Daerah Istimewa Yogyakarta'
}


def load_data(csv_path="data/dataset_sosial_ekonomi.csv"):
    """
    Memuat dataset utama dari CSV dengan error handling yang informatif.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File dataset tidak ditemukan di path: '{csv_path}'. Pastikan path relatif sudah benar.")
    df = pd.read_csv(csv_path)
    return df


def load_geojson(geojson_path="geojson/indonesia-38-provinces.geojson"):
    """
    Memuat file GeoJSON batas wilayah Indonesia 38 provinsi.
    Menetapkan root 'id' untuk setiap feature agar pemetaan lokasi di Plotly 100% presisi.
    """
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"File GeoJSON tidak ditemukan di path: '{geojson_path}'. Pastikan path relatif sudah benar.")
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
        
    for feat in geojson_data.get('features', []):
        feat['id'] = feat.get('properties', {}).get('PROVINSI')
        
    return geojson_data


def standardize_provinces(df):
    """
    Menstandarisasi penamaan provinsi agar 100% cocok dengan GeoJSON.
    Membuat kolom 'Provinsi_Geo' khusus untuk keperluan join geospatial,
    sambil tetap mempertahankan kolom 'Provinsi' asli.
    """
    df_clean = df.copy()
    df_clean['Provinsi_Geo'] = df_clean['Provinsi'].str.strip().replace(PROVINCE_NAME_MAPPING)
    return df_clean


def validate_dataset(df, geojson_data=None):
    """
    Melakukan audit dan validasi otomatis menyeluruh terhadap dataset dan GeoJSON.
    Mengembalikan dictionary status validasi, daftar pengecekan, serta detail pesan.
    """
    checks = []
    is_valid = True

    # 1. Validasi Jumlah Baris (Provinsi)
    n_rows = len(df)
    check_rows = {
        'name': 'Jumlah Provinsi Lengkap (38 Provinsi)',
        'expected': '38 Provinsi',
        'actual': f'{n_rows} Provinsi',
        'status': n_rows == 38,
        'message': 'Seluruh 38 provinsi di Indonesia (termasuk 4 provinsi baru pemekaran Papua) tercakup lengkap.' if n_rows == 38 else f'Jumlah baris ({n_rows}) tidak sesuai target 38 provinsi!'
    }
    checks.append(check_rows)
    if not check_rows['status']:
        is_valid = False

    # 2. Validasi Keunikan Provinsi & Kode
    dup_prov = df['Provinsi'].duplicated().sum()
    dup_kode = df['Kode_Provinsi'].duplicated().sum()
    check_dup = {
        'name': 'Keunikan Provinsi & Kode Wilayah',
        'expected': '0 Duplikasi',
        'actual': f'{dup_prov} Dup Provinsi, {dup_kode} Dup Kode',
        'status': (dup_prov == 0 and dup_kode == 0),
        'message': 'Setiap baris merupakan entitas provinsi yang unik tanpa duplikasi.' if (dup_prov == 0 and dup_kode == 0) else 'Ditemukan duplikasi pada data!'
    }
    checks.append(check_dup)
    if not check_dup['status']:
        is_valid = False

    # 3. Validasi Missing Value
    total_null = df.isnull().sum().sum()
    check_null = {
        'name': 'Kelengkapan Data (Missing Values)',
        'expected': '0 Missing Values',
        'actual': f'{total_null} Missing Values',
        'status': total_null == 0,
        'message': 'Seluruh sel data terisi lengkap tanpa missing value / NaN.' if total_null == 0 else f'Ditemukan {total_null} nilai kosong!'
    }
    checks.append(check_null)
    if not check_null['status']:
        is_valid = False

    # 4. Validasi 9 Indikator Numerik
    req_numeric = list(INDICATOR_METADATA.keys())
    missing_cols = [c for c in req_numeric if c not in df.columns]
    check_cols = {
        'name': 'Ketersediaan Indikator Numerik (>= 8 variabel)',
        'expected': 'Minimal 8 Indikator Numerik',
        'actual': f'{len(req_numeric) - len(missing_cols)} Indikator Tersedia',
        'status': len(missing_cols) == 0,
        'message': 'Tersedia 9 indikator sosial-ekonomi (melebihi batas minimal 8 variabel UAS).' if len(missing_cols) == 0 else f'Indikator tidak lengkap: {missing_cols}'
    }
    checks.append(check_cols)
    if not check_cols['status']:
        is_valid = False

    # 5. Validasi Kecocokan dengan Poligon GeoJSON
    if geojson_data:
        features = geojson_data.get('features', [])
        geo_prov_names = {f.get('properties', {}).get('PROVINSI') for f in features}
        df_geo_names = set(df['Provinsi_Geo'] if 'Provinsi_Geo' in df.columns else df['Provinsi'])
        unmatched_in_csv = df_geo_names - geo_prov_names
        unmatched_in_geo = geo_prov_names - df_geo_names
        geo_matched = len(df_geo_names.intersection(geo_prov_names))
        
        check_geo = {
            'name': 'Kecocokan Geometri Peta GeoJSON',
            'expected': '38/38 Poligon Cocok (100%)',
            'actual': f'{geo_matched}/38 Poligon Cocok',
            'status': (geo_matched == 38 and len(unmatched_in_csv) == 0 and len(unmatched_in_geo) == 0),
            'message': 'Semua 38 provinsi di CSV terhubung sempurna (100%) dengan poligon batas wilayah GeoJSON.' if geo_matched == 38 else f'Ketidakcocokan: CSV={unmatched_in_csv}, GeoJSON={unmatched_in_geo}'
        }
        checks.append(check_geo)
        if not check_geo['status']:
            is_valid = False

    return {'is_valid': is_valid, 'checks': checks}
