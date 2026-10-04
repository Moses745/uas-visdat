# Indonesia 2025: Potret Pembangunan Sosial-Ekonomi
### Proyek Ujian Akhir Semester (UAS) — Visualisasi Data dan Informasi
**Politeknik Statistika STIS — Tahun Akademik 2025/2026**

Aplikasi visualisasi data interaktif berformat **Interactive Web Story (Scrollytelling)** yang memotret kondisi sosial-ekonomi 38 provinsi di Indonesia pada tahun 2025 (pasca peresmian empat Daerah Otonom Baru di Tanah Papua).

---

## 1. Deskripsi Proyek
Proyek ini dirancang sebagai sebuah **data story interaktif yang mengalir (scrollytelling)**, di mana pembaca cukup menggulir (*scroll*) dari atas ke bawah untuk menyimak alur cerita dari potret makro nasional hingga detail mikro provinsi. Dibangun dengan memadukan prinsip-prinsip komunikasi data visual, estetika modern, dan kaidah kartografi data akademik STIS, aplikasi ini menyajikan wawasan mendalam mengenai disparitas kewilayahan, korelasi antardimensi, dan struktur hierarki ekonomi nusantara.

---

## 2. Alur Cerita Data Storytelling (Bab 1 – Bab 5)
1. **Bab 1 — Lanskap Makro: Menatap Indonesia 2025**:
   - Hero section dengan temuan utama (*key finding hook*) dan tombol navigasi baca.
   - Ringkasan kartu metrik nasional (IPM, Tingkat Kemiskinan, PDRB per Kapita, TPT) berlabel rata-rata 38 provinsi (tidak berbobot penduduk) beserta catatan kaki metodologis.
   - Audit otomatis integritas dataset (*expander* validasi otomatis).
   - Tabel ringkasan statistik deskriptif untuk 9 indikator pembangunan.
2. **Bab 2 — Dimensi Spasial: Di Mana Posisi Setiap Provinsi?**:
   - Peta tematik interaktif 38 provinsi menggunakan `px.choropleth_map` modern (Plotly >= 5.24) dengan auto-centering pulau dan skala warna global (*cmin/cmax 38 provinsi*) agar perbandingan antarfilter valid.
   - Perilaku filter pulau bertipe **menyorot (highlight)**: provinsi di luar pulau terpilih diredam (*opacity* rendah, warna abu) sehingga konteks 38 provinsi tetap utuh.
   - Diagram batang komparatif terurut untuk variabel agregat mutlak (PDRB Total ADHK & Penduduk Miskin) dengan tombol animasi ▶ "Putar Pertumbuhan Batang" guna menghindari *area bias* kartografi.
   - Kalimat *Takeaway* analitis otomatis di bawah setiap grafik.
3. **Bab 3 — Dimensi Multivariat: Mengurai Pola dan Keterkaitan Antarindikator**:
   - *Scatterplot Interaktif*: Pilihan bebas sumbu X & Y dengan garis tren linear OLS, nilai $R^2$, korelasi Pearson, pencegahan $X=Y$, penanganan $n<3$, serta anotasi otomatis provinsi sorotan Bab 5 (DKI Jakarta, DIY, Bali, Papua Tengah).
   - *Matriks Korelasi (Heatmap 9 Indikator)*: Peta korelasi Pearson lengkap dengan palet divergen `RdBu_r`.
   - *Principal Component Analysis (PCA)*: Standardisasi fitur (`StandardScaler`), 2D Biplot dengan vektor loading indikator dominan yang diturunkan secara dinamis, dan Scree plot varians.
   - *Parallel Coordinates Plot*: Profil multidimensi 38 provinsi dengan interaktivitas penapisan rentang nilai (*brushing*) dan penyorot profil provinsi terpilih.
   - *Tipologi Klaster Wilayah (K-Means, $k=4$)*: Pengelompokan empiris ke dalam 4 tipologi sosial-ekonomi unik dengan justifikasi kurva Elbow & skor Silhouette.
4. **Bab 4 — Dimensi Hierarkis: Struktur Kewilayahan Nusantara**:
   - Struktur 3 tingkat: *Indonesia → Pulau/Wilayah → Provinsi*.
   - Representasi ganda: **Treemap** (kotak bersarang) dan **Sunburst** (radial konsentris) dengan fitur navigasi interaktif.
   - Pengkodean visual terjustifikasi: Luas sektor **wajib menggunakan variabel agregat aditif** (PDRB Total ADHK / Jumlah Penduduk Miskin) untuk mencegah bias agregasi rasio, dan warna gradien kontinu mewakili IPM.
5. **Bab 5 — Sintesis Analitik & Epilog: Apa yang Dapat Kita Pelajari?**:
   - Lima wawasan mendalam berbasis data empiris terhitung dinamis: polarisasi spasial Barat vs Timur, fenomena *enclave economy* tambang (Papua Tengah & Papua Barat), dinamika pasar kerja agraris vs urban, anomali DI Yogyakarta & Bali, serta implikasi kebijakan berbasis bukti (*targeted policy*).
   - Bagian komprehensif Metodologi & Keterbatasan Data (data *cross-section*, ukuran sampel $n=38$, implikasi DOB Papua, dan definisi operasional 9 indikator BPS).

---

## 3. Data & Metadata
- **Dataset Utama BPS**: `data/dataset_sosial_ekonomi.csv`
  - **Sumber**: Badan Pusat Statistik (BPS) Republik Indonesia tahun 2025.
  - **Cakupan**: 38 Provinsi di Indonesia (100% lengkap tanpa missing values / duplikasi).
  - **9 Indikator Numerik**:
    1. *Indeks Pembangunan Manusia (IPM)* (Poin)
    2. *PDRB per Kapita (Harga Berlaku)* (Ribu Rp)
    3. *Tingkat Kemiskinan (%)*
    4. *Jumlah Penduduk Miskin* (Ribu Jiwa)
    5. *Tingkat Pengangguran Terbuka (TPT)* (%)
    6. *Tingkat Partisipasi Angkatan Kerja (TPAK)* (%)
    7. *TPK Hotel Berbintang* (%)
    8. *TPK Hotel Nonbintang* (%)
    9. *PDRB Total Riil (ADHK)* (Miliar Rp)
- **Data Pendukung Spasial**: `geojson/indonesia-38-provinces.geojson`
  - **Sumber**: Repositori Terbuka GeoJSON Batas 38 Provinsi Indonesia.
  - Standardisasi otomatis penamaan *DI Yogyakarta* ke *Daerah Istimewa Yogyakarta* sehingga join data 100% presisi.

---

## 4. Teknologi yang Digunakan
- **Python** (versi 3.10+)
- **Streamlit** (>=1.40.0): Kerangka kerja aplikasi web dengan arsitektur `@st.fragment` untuk isolasi re-render widget interaktif.
- **Pandas & NumPy**: Manipulasi, transformasi, dan kalkulasi data.
- **Plotly** (>=5.24.0): Visualisasi grafis interaktif modern (`px.choropleth_map`, Scatterplot, Biplot, Treemap, Sunburst, Parcoords, Heatmap) dengan transisi animasi halus (`uirevision` stabil).
- **Scikit-learn**: Normalisasi fitur (`StandardScaler`), reduksi dimensi PCA, dan K-Means clustering.

---

## 5. Fitur Interaktivitas, Animasi & Aksesibilitas
- **Scroll Reveal Animation (sekali tampil)**: Efek fade-in halus saat elemen (kartu metrik, bridge, kartu wawasan) memasuki viewport.
- **Reading Progress Bar**: Bar progres membaca fixed di bagian atas halaman.
- **Floating Back-to-Top Button**: Tombol kembali ke atas yang muncul otomatis saat halaman digulir.
- **Scroll-Spy & Smooth Navigation**: Tautan Daftar Isi di sidebar secara otomatis menyorot bab yang sedang dibaca.
- **Chapter Opener Transition**: Setiap bab dibuka dengan panel yang menyapu dari kiri, angka bab raksasa meluncur masuk, teks muncul berurutan, serta pill penanda bab yang muncul sekali saat bab pertama kali dimasuki.
- **Sub-bab Transition (Bab 3)**: Header sub-bab 3.1–3.4 beranimasi (chip nomor, judul slide-in, garis menjalar), peta sub-bab berpenanda aktif, dan kotak transisi dengan garis aksen yang menjalar serta panah penuntun.
- **Count-Up Animation**: Animasi angka berhitung pada kartu metrik Bab 1.
- **Aksesibilitas Gerak**: Seluruh animasi dan transisi secara otomatis dinonaktifkan jika pengguna mengaktifkan preferensi sistem `prefers-reduced-motion: reduce`.

---

## 6. Struktur Berkas
```text
uas-visdat/
│
├── .streamlit/
│   └── config.toml                     # Konfigurasi tema terang & UI bersih Streamlit
│
├── app.py                              # Aplikasi utama Streamlit (Interactive Web Story)
├── requirements.txt                    # Dependensi Python untuk instalasi & deployment
├── README.md                           # Dokumentasi lengkap proyek
├── .gitignore                          # Berkas pengabaian Git (__pycache__, venv, dll)
│
├── data/
│   └── dataset_sosial_ekonomi.csv      # Dataset BPS 2025 (38 provinsi)
│
├── geojson/
│   └── indonesia-38-provinces.geojson  # GeoJSON batas wilayah 38 provinsi
│
├── utils/
│   ├── __init__.py
│   ├── preprocessing.py                # Pemuatan data, standardisasi nama, & validasi
│   ├── analysis.py                     # Statistik deskriptif, korelasi, PCA, & clustering
│   └── visualizations.py               # Generator visualisasi Plotly interaktif
│
└── assets/
    └── style.css                       # Desain CSS khusus Scrollytelling modern
```

---

## 7. Panduan Menjalankan Aplikasi

### Langkah 1: Pindah ke Direktori Proyek
```bash
cd uas-visdat
```

### Langkah 2: Pasang Dependensi
```bash
pip install -r requirements.txt
```

### Langkah 3: Jalankan Aplikasi
```bash
streamlit run app.py
```
Aplikasi akan langsung terbuka di browser Anda pada alamat `http://localhost:8501`.

---

## 8. Panduan Deployment ke Streamlit Community Cloud (Gratis)
Seluruh jalur berkas di dalam aplikasi telah menggunakan **relative path** (`data/...` dan `geojson/...`) sehingga siap di-deploy secara instan.

1. **Push ke GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Proyek UAS Visualisasi Data STIS - Indonesia 2025"
   git branch -M main
   git remote add origin https://github.com/<username-anda>/uas-visdat.git
   git push -u origin main
   ```
2. **Buka Streamlit Community Cloud**:
   - Kunjungi [share.streamlit.io](https://share.streamlit.io/) dan login dengan akun GitHub Anda.
   - Klik **"New app"**.
   - Pilih repositori `uas-visdat`, branch `main`, dan set Main file path ke `app.py`.
   - Klik **"Deploy!"**.


---

## 5. Animasi & Interaksi Klien (`assets/story.js`)
Seluruh logika animasi sisi klien berada di `assets/story.js` (disuntikkan oleh `app.py`) dan gayanya di `assets/style.css`.

- **Animasi saat filter/dropdown berganti**: `app.py` menaruh penanda tak terlihat `chart_sig(...)` sebelum tiap grafik. Ketika filter berubah, `story.js` memainkan efek sesuai jenis grafik: `morph` (titik scatter/PCA/klaster bergeser & berubah ukuran), `grow` (batang tumbuh), `cascade` (irisan treemap/sunburst muncul berurutan), `focus` (peta & tabel redup lalu menajam). Tambahkan `chart_sig("nama_unik", filter1, filter2, fx="...")` tepat sebelum grafik baru agar ikut beranimasi.
- **Animasi kemunculan sekali saja**: status "sudah dilihat" disimpan per kunci elemen (bukan per node DOM), sehingga tidak diulang ketika pengguna scroll naik-turun maupun ketika Streamlit mengganti node setelah filter berubah. Elemen yang baru pertama kali muncul saat scroll ke atas ditampilkan langsung tanpa animasi.
- **Penanda bab**: setiap bab dibuka dengan ubin nomor "BAB n" + penelusur "n dari 5" (`chapter_opener(...)` di `app.py`), dan indikator bab permanen di kanan atas selama membaca.
- Transisi bawaan Plotly dimatikan (`NATIVE_TRANSITION_MS = 0` di `utils/visualizations.py`) agar tidak bentrok dengan animasi `story.js`.
