import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
"""
utils/analysis.py
Modul analisis statistik deskriptif, korelasi bivariat, PCA, dan K-Means clustering.
Proyek UAS Visualisasi Data dan Informasi - Politeknik Statistika STIS
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

from .preprocessing import INDICATOR_METADATA

def get_numeric_indicators():
    return list(INDICATOR_METADATA.keys())

def compute_summary_statistics(df):
    """
    Menghitung ringkasan statistik deskriptif untuk setiap indikator numerik
    beserta provinsi dengan nilai minimum dan maksimum.
    """
    num_cols = get_numeric_indicators()
    stats_rows = []
    
    for col in num_cols:
        meta = INDICATOR_METADATA[col]
        mean_val = df[col].mean()
        median_val = df[col].median()
        std_val = df[col].std()
        min_val = df[col].min()
        max_val = df[col].max()
        
        min_prov = df.loc[df[col] == min_val, 'Provinsi'].values[0]
        max_prov = df.loc[df[col] == max_val, 'Provinsi'].values[0]
        
        stats_rows.append({
            'Indikator': meta['label'],
            'Satuan': meta['unit'],
            'Rata-rata': mean_val,
            'Median': median_val,
            'Standar Deviasi': std_val,
            'Minimum': min_val,
            'Provinsi Minimum': min_prov,
            'Maksimum': max_val,
            'Provinsi Maksimum': max_prov,
            'Kolom': col
        })
        
    return pd.DataFrame(stats_rows)

def compute_national_overview_cards(df):
    """
    Menghasilkan ringkasan kartu metrik nasional utama untuk halaman Overview.
    """
    # IPM
    ipm_mean = df['IPM_2025'].mean()
    ipm_max = df.loc[df['IPM_2025'].idxmax()]
    ipm_min = df.loc[df['IPM_2025'].idxmin()]
    
    # Kemiskinan
    pov_mean = df['Kemiskinan_September_2025_persen'].mean()
    pov_max = df.loc[df['Kemiskinan_September_2025_persen'].idxmax()]
    pov_min = df.loc[df['Kemiskinan_September_2025_persen'].idxmin()]
    
    # PDRB per Kapita
    pdrb_mean = df['PDRB_per_Kapita_HB_2025_ribu_Rp'].mean() / 1000  # dalam juta
    pdrb_max = df.loc[df['PDRB_per_Kapita_HB_2025_ribu_Rp'].idxmax()]
    pdrb_min = df.loc[df['PDRB_per_Kapita_HB_2025_ribu_Rp'].idxmin()]

    # TPT
    tpt_mean = df['TPT_Agustus_2025_persen'].mean()
    tpt_max = df.loc[df['TPT_Agustus_2025_persen'].idxmax()]
    tpt_min = df.loc[df['TPT_Agustus_2025_persen'].idxmin()]

    return {
        'total_provinces': len(df),
        'ipm': {
            'mean': ipm_mean,
            'max_val': ipm_max['IPM_2025'],
            'max_prov': ipm_max['Provinsi'],
            'min_val': ipm_min['IPM_2025'],
            'min_prov': ipm_min['Provinsi']
        },
        'kemiskinan': {
            'mean': pov_mean,
            'max_val': pov_max['Kemiskinan_September_2025_persen'],
            'max_prov': pov_max['Provinsi'],
            'min_val': pov_min['Kemiskinan_September_2025_persen'],
            'min_prov': pov_min['Provinsi']
        },
        'pdrb_per_kapita': {
            'mean_juta': pdrb_mean,
            'max_val_juta': pdrb_max['PDRB_per_Kapita_HB_2025_ribu_Rp'] / 1000,
            'max_prov': pdrb_max['Provinsi'],
            'min_val_juta': pdrb_min['PDRB_per_Kapita_HB_2025_ribu_Rp'] / 1000,
            'min_prov': pdrb_min['Provinsi']
        },
        'tpt': {
            'mean': tpt_mean,
            'max_val': tpt_max['TPT_Agustus_2025_persen'],
            'max_prov': tpt_max['Provinsi'],
            'min_val': tpt_min['TPT_Agustus_2025_persen'],
            'min_prov': tpt_min['Provinsi']
        }
    }

def compute_correlation_matrix(df, cols=None):
    """
    Menghitung matriks korelasi Pearson antar indikator numerik.
    """
    if cols is None:
        cols = get_numeric_indicators()
    labels = [INDICATOR_METADATA[c]['label'] for c in cols]
    corr_df = df[cols].corr()
    corr_df.index = labels
    corr_df.columns = labels
    return corr_df

def perform_pca_analysis(df, feature_cols=None, n_components=2):
    """
    Melakukan Principal Component Analysis (PCA) setelah standardisasi fitur menggunakan StandardScaler.
    Mengembalikan koordinat PC1, PC2, explained variance, serta matrix loading untuk biplot.
    """
    if feature_cols is None:
        feature_cols = [
            'IPM_2025',
            'PDRB_per_Kapita_HB_2025_ribu_Rp',
            'Kemiskinan_September_2025_persen',
            'Penduduk_Miskin_September_2025_ribu',
            'TPT_Agustus_2025_persen',
            'TPAK_Agustus_2025_persen',
            'TPK_Hotel_Berbintang_2025_persen',
            'TPK_Hotel_Nonbintang_2025_persen',
            'PDRB_Total_ADHK_2025_miliar_Rp'
        ]
    
    X = df[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(X_scaled)
    
    pca_df = df[['Provinsi', 'Pulau_Wilayah', 'Hierarki_Level_2', 'IPM_2025', 'PDRB_per_Kapita_HB_2025_ribu_Rp', 'Kemiskinan_September_2025_persen']].copy()
    pca_df['PC1'] = components[:, 0]
    pca_df['PC2'] = components[:, 1]
    
    exp_var = pca.explained_variance_ratio_
    var_pc1 = exp_var[0] * 100
    var_pc2 = exp_var[1] * 100
    total_var = (exp_var[0] + exp_var[1]) * 100
    
    # Loadings (korelasi antara fitur asli dengan komponen utama)
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    loadings_df = pd.DataFrame({
        'Indikator': [INDICATOR_METADATA[c]['label'] for c in feature_cols],
        'Kolom': feature_cols,
        'PC1_Component': pca.components_[0, :],
        'PC2_Component': pca.components_[1, :],
        'Loading_PC1': loadings[:, 0],
        'Loading_PC2': loadings[:, 1]
    }, index=feature_cols)

    # Identifikasi indikator dominan secara dinamis berdasarkan nilai loading absolut tertinggi
    top_pc1_pos = loadings_df.sort_values(by='Loading_PC1', ascending=False).iloc[0]
    top_pc1_neg = loadings_df.sort_values(by='Loading_PC1', ascending=True).iloc[0]
    top_pc2_pos = loadings_df.sort_values(by='Loading_PC2', ascending=False).iloc[0]
    top_pc2_neg = loadings_df.sort_values(by='Loading_PC2', ascending=True).iloc[0]

    # Ambil 3 loading terbesar untuk PC1 dan PC2
    top3_pc1 = loadings_df.assign(abs_loading=loadings_df['Loading_PC1'].abs()).sort_values(by='abs_loading', ascending=False).head(3)
    top3_pc2 = loadings_df.assign(abs_loading=loadings_df['Loading_PC2'].abs()).sort_values(by='abs_loading', ascending=False).head(3)
    
    return {
        'pca_df': pca_df,
        'loadings_df': loadings_df,
        'var_pc1': var_pc1,
        'var_pc2': var_pc2,
        'total_var': total_var,
        'pca_model': pca,
        'feature_cols': feature_cols,
        'scaler': scaler,
        'top_pc1_pos': top_pc1_pos,
        'top_pc1_neg': top_pc1_neg,
        'top_pc2_pos': top_pc2_pos,
        'top_pc2_neg': top_pc2_neg,
        'top3_pc1': top3_pc1,
        'top3_pc2': top3_pc2
    }

def compute_cluster_validation_metrics(df, feature_cols=None, k_range=range(2, 8)):
    """
    Menghitung evaluasi Elbow (Inertia/WSS) dan Silhouette Score untuk rentang k (default 2-7).
    Digunakan sebagai bukti empiris pemilihan k=4.
    """
    from sklearn.metrics import silhouette_score
    if feature_cols is None:
        feature_cols = [
            'IPM_2025',
            'PDRB_per_Kapita_HB_2025_ribu_Rp',
            'Kemiskinan_September_2025_persen',
            'TPT_Agustus_2025_persen',
            'TPAK_Agustus_2025_persen'
        ]
    X = df[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    metrics = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia = km.inertia_
        sil = silhouette_score(X_scaled, labels)
        metrics.append({
            'k': k,
            'Inersia (WSS)': round(inertia, 2),
            'Silhouette Score': round(sil, 3)
        })
    return pd.DataFrame(metrics)

def perform_kmeans_clustering(df, feature_cols=None, n_clusters=4):
    """
    Melakukan clustering provinsi berbasis indikator terstandarisasi untuk mendeteksi
    tipologi wilayah sosial-ekonomi tanpa bias subjektif.
    Memberikan label yang unik, deskriptif, dan berbasis profil centroid.
    """
    if feature_cols is None:
        feature_cols = [
            'IPM_2025',
            'PDRB_per_Kapita_HB_2025_ribu_Rp',
            'Kemiskinan_September_2025_persen',
            'TPT_Agustus_2025_persen',
            'TPAK_Agustus_2025_persen'
        ]
        
    X = df[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    res_df = df.copy()
    res_df['Cluster'] = clusters
    
    # Hitung profil rata-rata masing-masing klaster
    cluster_profile = res_df.groupby('Cluster')[feature_cols].mean()

    # Tentukan label deskriptif yang unik berdasarkan karakteristik pembeda tiap klaster
    # Cek klaster dengan ciri khas spesifik
    poverty_ranks = cluster_profile['Kemiskinan_September_2025_persen'].rank(ascending=False)
    pdrb_ranks = cluster_profile['PDRB_per_Kapita_HB_2025_ribu_Rp'].rank(ascending=False)
    tpt_ranks = cluster_profile['TPT_Agustus_2025_persen'].rank(ascending=False)
    
    label_dict = {}
    short_label_dict = {}
    for c in range(n_clusters):
        p_val = cluster_profile.loc[c, 'Kemiskinan_September_2025_persen']
        pdrb_val = cluster_profile.loc[c, 'PDRB_per_Kapita_HB_2025_ribu_Rp']
        tpt_val = cluster_profile.loc[c, 'TPT_Agustus_2025_persen']
        
        # Klaster Kemiskinan Tertinggi / DOB Papua
        if poverty_ranks[c] == 1:
            lbl = f"Klaster {c+1}: Tantangan Struktural & Kemiskinan Ekstrem (DOB Papua)"
            short_lbl = f"K{c+1}: Tantangan Struktural (DOB)"
        # Klaster Output Ekonomi Tertinggi
        elif pdrb_ranks[c] == 1:
            lbl = f"Klaster {c+1}: Sentra Ekonomi Maju (Metropolitan & Lumbung Tambang)"
            short_lbl = f"K{c+1}: Sentra Ekonomi Maju"
        # Klaster Pengangguran Tertinggi
        elif tpt_ranks[c] == 1:
            lbl = f"Klaster {c+1}: Transisi Tenaga Kerja (TPT Tinggi & Kemiskinan Moderat)"
            short_lbl = f"K{c+1}: Transisi Kerja / TPT Tinggi"
        # Klaster Seimbang / Agraris
        else:
            lbl = f"Klaster {c+1}: Berkembang Sedang (Pasar Kerja Aktif & Kemiskinan Rendah)"
            short_lbl = f"K{c+1}: Berkembang Sedang"
            
        label_dict[c] = lbl
        short_label_dict[c] = short_lbl
            
    res_df['Tipologi_Klaster'] = res_df['Cluster'].map(label_dict)
    res_df['Tipologi_Klaster_Singkat'] = res_df['Cluster'].map(short_label_dict)
    return res_df, label_dict, cluster_profile

