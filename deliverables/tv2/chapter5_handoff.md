# Chương 5 — thí nghiệm mới LIVE_MEASURED

## 5.1 Môi trường thực nghiệm

{
  "timestamp": "2026-11-08T12:47:48.523744",
  "os": "Windows 11 (build 10.0.26200)",
  "machine": "AMD64",
  "processor": "Intel64 Family 6 Model 197 Stepping 2, GenuineIntel",
  "cpu_logical_cores": 14,
  "python_version": "3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)]",
  "psycopg_version": "3.3.6",
  "postgresql_version": "PostgreSQL 18.3 on x86_64-windows, compiled by msvc-19.44.35225, 64-bit",
  "server_version_num": "180003",
  "database": "real_estate_db",
  "user": "postgres",
  "client_encoding": "UTF8",
  "timezone": "Asia/Bangkok",
  "collation": {
    "datcollate": "English_United States.1252",
    "datctype": "English_United States.1252"
  },
  "pg_settings": {
    "default_statistics_target": {
      "setting": "100",
      "unit": null,
      "source": "default"
    },
    "effective_cache_size": {
      "setting": "524288",
      "unit": "8kB",
      "source": "default"
    },
    "effective_io_concurrency": {
      "setting": "16",
      "unit": null,
      "source": "default"
    },
    "enable_bitmapscan": {
      "setting": "on",
      "unit": null,
      "source": "default"
    },
    "enable_indexonlyscan": {
      "setting": "on",
      "unit": null,
      "source": "default"
    },
    "enable_indexscan": {
      "setting": "on",
      "unit": null,
      "source": "default"
    },
    "enable_seqscan": {
      "setting": "on",
      "unit": null,
      "source": "default"
    },
    "jit": {
      "setting": "on",
      "unit": null,
      "source": "default"
    },
    "maintenance_work_mem": {
      "setting": "65536",
      "unit": "kB",
      "source": "default"
    },
    "max_parallel_workers": {
      "setting": "8",
      "unit": null,
      "source": "default"
    },
    "max_parallel_workers_per_gather": {
      "setting": "2",
      "unit": null,
      "source": "default"
    },
    "random_page_cost": {
      "setting": "4",
      "unit": null,
      "source": "default"
    },
    "seq_page_cost": {
      "setting": "1",
      "unit": null,
      "source": "default"
    },
    "shared_buffers": {
      "setting": "16384",
      "unit": "8kB",
      "source": "configuration file"
    },
    "track_io_timing": {
      "setting": "off",
      "unit": null,
      "source": "default"
    },
    "work_mem": {
      "setting": "4096",
      "unit": "kB",
      "source": "default"
    }
  }
}

## 5.2 Vận hành hệ thống

Experiment `62ea434decd44713b3752af152f81de8`: 3 quy mô, 10 cấu hình, 3 warm-up và 20 lượt chính thức. Importer production, kiểm tra rollback 50K và fingerprint được lưu trong evidence. Database real_estate_db độc lập; khóa SHARE trong mỗi quy mô chặn writer khác. Settings session đo và catalog/equivalence từng cấu hình có trong evidence.

## 5.3 Kết quả Q1–Q4

- 50000 / Q1_baseline: median 21.7635 ms, IQR 20.156 ms, speedup 1.000.
- 50000 / Q1_indexed: median 1.406 ms, IQR 0.544 ms, speedup 15.479.
- 50000 / Q2_baseline: median 25.616 ms, IQR 15.9725 ms, speedup 1.000.
- 50000 / Q2_indexed: median 0.1685 ms, IQR 0.0445 ms, speedup 152.024.
- 50000 / Q3_A: median 12.689 ms, IQR 6.5955 ms, speedup 1.000.
- 50000 / Q3_B: median 14.9245 ms, IQR 9.674 ms, speedup 0.850.
- 50000 / Q3_C: median 10.826 ms, IQR 1.8755 ms, speedup 1.172.
- 50000 / Q3_D: median 0.467 ms, IQR 0.1425 ms, speedup 27.171.
- 50000 / Q4_baseline: median 31.6305 ms, IQR 13.4585 ms, speedup 1.000.
- 50000 / Q4_indexed: median 34.054 ms, IQR 10.4185 ms, speedup 0.929.
- 200000 / Q1_baseline: median 44.508 ms, IQR 30.9825 ms, speedup 1.000.
- 200000 / Q1_indexed: median 6.532 ms, IQR 2.6605 ms, speedup 6.814.
- 200000 / Q2_baseline: median 805.738 ms, IQR 393.0405 ms, speedup 1.000.
- 200000 / Q2_indexed: median 0.1445 ms, IQR 0.0415 ms, speedup 5576.042.
- 200000 / Q3_A: median 173.4115 ms, IQR 113.0425 ms, speedup 1.000.
- 200000 / Q3_B: median 181.568 ms, IQR 91.8895 ms, speedup 0.955.
- 200000 / Q3_C: median 134.167 ms, IQR 62.3315 ms, speedup 1.293.
- 200000 / Q3_D: median 2.2045 ms, IQR 0.56 ms, speedup 78.663.
- 200000 / Q4_baseline: median 183.9545 ms, IQR 98.6585 ms, speedup 1.000.
- 200000 / Q4_indexed: median 202.8995 ms, IQR 113.7565 ms, speedup 0.907.
- 500000 / Q1_baseline: median 238.4975 ms, IQR 163.311 ms, speedup 1.000.
- 500000 / Q1_indexed: median 50.652 ms, IQR 70.85 ms, speedup 4.709.
- 500000 / Q2_baseline: median 266.1755 ms, IQR 168.616 ms, speedup 1.000.
- 500000 / Q2_indexed: median 0.1285 ms, IQR 0.0375 ms, speedup 2071.405.
- 500000 / Q3_A: median 292.9045 ms, IQR 179.838 ms, speedup 1.000.
- 500000 / Q3_B: median 115.334 ms, IQR 18.634 ms, speedup 2.540.
- 500000 / Q3_C: median 134.6745 ms, IQR 16.124 ms, speedup 2.175.
- 500000 / Q3_D: median 3.7085 ms, IQR 0.491 ms, speedup 78.982.
- 500000 / Q4_baseline: median 150.003 ms, IQR 10.675 ms, speedup 1.000.
- 500000 / Q4_indexed: median 389.8545 ms, IQR 201.6045 ms, speedup 0.385.

## 5.4 Khả năng mở rộng

Xem [scaling_analysis](tables/scaling_analysis.md) và [FIG03](figures/FIG03.png). Tỷ lệ latency được tính so với 50K; ba tập là prefix nên không phải các mẫu độc lập.

## 5.5 Giải thích kết quả

Xem [Q3 factorial](tables/q3_factorial_analysis.md): A/B và C/D tách rewriting; A/C và B/D tách index. [FIG06](figures/FIG06.png) đếm node scan thực sự, không đếm truy vấn. Q4 là đối chứng, không giả định index luôn nhanh hơn. [index_analysis](tables/index_analysis.md) ghi index usage và dung lượng.

## 5.6 Hạn chế thực nghiệm

Revision upstream chưa chứng minh; SHA CSV chỉ khóa đầu vào hiện tại. Thí nghiệm warm-cache, không cold-cache; EXPLAIN có overhead. Chưa kiểm soát toàn bộ tải nền, autovacuum và nhiễu hệ điều hành; IQR và min/max phải đi kèm median. Không trộn với 600 plan lịch sử. Chưa nghiệm thu browser/visual QA mới; không khẳng định tính tổng quát ngoài máy và workload này.
