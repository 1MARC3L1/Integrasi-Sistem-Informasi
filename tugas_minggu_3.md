# Tugas Minggu 3

**Nama:** Marcel Christian Effruan  
**NIM:** 2415354048  
**Mata Kuliah:** Integrasi Sistem Informasi  
**Topik:** Implementasi Sistem Legacy & EAI / Early SOA (HTTP + XML)

## 1. Analisis Pola Arsitektur

Rancangan ini termasuk Adapter Pattern karena program C hanya bisa membaca dan menulis file teks lokal dan tidak punya akses jaringan. Server `adapter_service.py` menjadi perantara yang menerjemahkan antarmuka modern (HTTP + XML) ke antarmuka internal sistem lama (file teks CSV), dan sebaliknya. Kode program C tidak diubah sama sekali. Seluruh kebutuhan integrasi, yaitu protokol jaringan, parsing, dan serialisasi XML, ditanggung adapter. Ini sesuai konsep wrapper dalam EAI: antarmuka yang tidak kompatibel dibungkus agar bisa dipakai klien lain.

Keuntungan untuk klien web:

- Loose coupling: klien cukup tahu endpoint (`GET/POST /students`) dan format XML, tidak perlu tahu format file legacy.
- Sistem legacy bisa diganti nanti (misalnya ke database) tanpa mengubah klien selama format XML tetap sama.
- Sistem lama tidak perlu dimodifikasi sehingga risikonya lebih kecil.
- HTTP dan XML bisa digunakan dari berbagai platform (curl, browser, Postman, aplikasi lain).
- Error dikembalikan dalam bentuk status HTTP (200, 201, 400, 404) dan pesan XML yang terstandar.

## 2. Analisis Overhead Serialisasi Data

Respons `GET /students/2415354001`:

```xml
<?xml version='1.0' encoding='utf-8'?>
<StudentResponse><NIM>2415354001</NIM><Nama>I Made Sujana</Nama><Jurusan>Teknologi Informasi</Jurusan><Status>ACTIVE</Status></StudentResponse>
```

**a. Data aktual**

| Data | Byte |
|---|---|
| `2415354001` | 10 |
| `I Made Sujana` | 13 |
| `Teknologi Informasi` | 19 |
| `ACTIVE` | 6 |
| **Total** | **48** |

**b. Total respons XML**

| Komponen | Byte |
|---|---|
| Deklarasi XML + newline | 39 |
| `<StudentResponse>` + `</StudentResponse>` | 17 + 18 = 35 |
| `<NIM>` + `</NIM>` | 5 + 6 = 11 |
| `<Nama>` + `</Nama>` | 6 + 7 = 13 |
| `<Jurusan>` + `</Jurusan>` | 9 + 10 = 19 |
| `<Status>` + `</Status>` | 8 + 9 = 17 |
| Data aktual | 48 |
| **Total (body + deklarasi)** | **182** |

Body saja, tanpa deklarasi, adalah 143 byte.

**c. Rasio overhead**

- Overhead = 182 − 48 = **134 byte**
- Terhadap total respons: 134 / 182 = **± 73,6%**
- Terhadap data aktual: 134 / 48 = **± 279%** (XML sekitar 3,8 kali lebih besar dari datanya)
- Tanpa deklarasi: 95 / 143 = ± 66,4% dari total body

Sebagai pembanding, satu baris di file teks hanya 51 byte (48 byte data + 3 koma), jadi XML kira-kira 3,5 kali lebih besar dari format penyimpanan aslinya. Harganya adalah muatan yang lebih besar, tetapi XML bersifat self-describing, bisa divalidasi skema, dan mudah dipakai lintas platform. Untuk volume besar, overhead ini terasa pada bandwidth dan waktu parsing.

Catatan: byte dihitung dengan encoding UTF-8. Semua karakter di sini ASCII sehingga 1 karakter = 1 byte.

## 3. Prediksi Keterbatasan Integrasi

Yang terjadi pada 500 POST simultan:

- `HTTPServer` bawaan Python bersifat single-threaded, sehingga request diproses satu per satu. Antrean koneksi cepat penuh, dan sebagian besar klien mengalami connection refused, reset, atau timeout. Data yang dikirim klien bisa hilang tanpa jejak.
- Jika server diubah ke multi-thread atau dijalankan lebih dari satu proses, beberapa penulis akan menulis ke `students_db.txt` bersamaan tanpa file locking. Terjadi race condition: baris bisa saling menyisip atau tercampur sehingga file korup. Program C yang menulis bersamaan juga tidak tahu ada penulis lain.
- Tidak ada validasi duplikasi NIM, transaksi, maupun rollback. Nama yang mengandung koma juga merusak format CSV.
- File teks tidak punya jaminan atomisitas dan konsistensi (tidak ada properti ACID).

Mengapa Message Broker dibutuhkan:

- Penyangga dan antrean: lonjakan request ditampung broker (misalnya RabbitMQ atau Kafka) sehingga tidak ada yang hilang.
- Serialisasi penulisan: satu consumer mengambil pesan berurutan dan menulis ke file legacy, sehingga tidak ada penulisan paralel.
- Decoupling asinkron: klien cukup menerima konfirmasi "diterima" tanpa menunggu sistem legacy yang lambat.
- Keandalan: broker mendukung persistensi pesan, acknowledgement, dan retry, sehingga data tidak hilang jika adapter atau sistem legacy sedang down.
- Skalabilitas: banyak produser bisa ditambah tanpa mengubah sistem legacy.

## Kesimpulan

Adapter Pattern memungkinkan sistem legacy berbahasa C terintegrasi dua arah dengan klien HTTP/XML tanpa mengubah kode sumbernya. Kelemahannya, overhead XML sekitar 73,6% dari total respons, dan penyimpanan file teks tidak aman untuk akses konkuren, sehingga diperlukan message broker atau database sungguhan.
