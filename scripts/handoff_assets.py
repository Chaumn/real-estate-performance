"""Portable historical presentation assets, derived from the packaged records."""
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


def complete_assets(output, rows, groups, status='HISTORICAL'):
    root = Path(__file__).resolve().parents[1]
    quality = json.loads((root/'results/build_report_500000.json').read_text())
    (output/'evidence/build_report.json').write_text(json.dumps(quality, indent=2), encoding='utf-8')
    titles = ['So sánh baseline và tối ưu', 'Speedup theo quy mô', 'Khả năng mở rộng',
              'Q3: Query Rewriting và Index', 'Q4: trường hợp đối chứng',
              'Scan type xuất hiện trong execution plans', 'Dung lượng index bổ sung',
              'NULL trong các dataset']
    for number, title in enumerate(titles, 1):
        fig, ax = plt.subplots(figsize=(12, 6))
        if number == 6:
            counts = Counter()
            def visit(node):
                if 'Scan' in node.get('Node Type', ''):
                    counts[node['Node Type']] += 1
                for child in node.get('Plans', []): visit(child)
            for plans in groups.values():
                for _, plan in plans: visit(plan[0]['Plan'])
            ax.bar(list(counts), list(counts.values()))
            ax.set_ylabel('Số node scan trong 600 plan (có thể nhiều node/plan)')
        elif number == 8:
            for column in ('price', 'district_name', 'ward_name'):
                scales = sorted(map(int, quality['outputs']))
                ax.plot(scales, [quality['outputs'][str(s)]['null_counts'][column]/s*100 for s in scales], marker='o', label=column)
            ax.set(xlabel='Số bản ghi', ylabel='Tỷ lệ NULL (%)')
            ax.legend()
        else:
            chosen = [r for r in rows if (number != 4 or r['query']=='Q3') and (number != 5 or r['query']=='Q4')]
            if number in (1, 2, 7):
                chosen = [r for r in chosen if r['configuration'] not in ('Q3_B','Q3_C')]
            metric = 'speedup' if number == 2 else 'index_bytes' if number == 7 else 'median_ms'
            for config in sorted({r['configuration'] for r in chosen}):
                records = sorted([r for r in chosen if r['configuration']==config], key=lambda r:r['scale'])
                ax.plot([r['scale'] for r in records], [r[metric] for r in records], marker='o', label=config)
            ax.set(xlabel='Số bản ghi', ylabel='Speedup (lần)' if number==2 else 'Dung lượng (byte)' if number==7 else 'Median Execution Time (ms)')
            ax.legend(fontsize=8, ncol=2)
        figure_status = 'DATASET_QUALITY_BUILD_REPORT' if number == 8 else status
        ax.set_title(f'FIG{number:02d} — {title}\n{figure_status} — xem giới hạn thực nghiệm trong bàn giao')
        ax.set_ylim(bottom=0); ax.grid(axis='y', alpha=.2); fig.tight_layout()
        for ext in ('png','svg'): fig.savefig(output/'figures'/f'FIG{number:02d}.{ext}', dpi=300)
        plt.close(fig)
    figure_readme = '# FIG01-FIG08\n\nGenerated PNG (300 DPI) and SVG. Browser/visual QA: NOT_RUN.\n\n'
    for number, title in enumerate(titles, 1):
        source = 'evidence/build_report.json' if number == 8 else 'evidence/benchmark_raw_plans.zip' if number == 6 else 'tables/benchmark_summary.csv'
        provenance = 'DATASET_QUALITY_BUILD_REPORT' if number == 8 else status
        figure_readme += f'- FIG{number:02d}: {title}; source: {source}; provenance: {provenance}.\n'
    (output/'figures/README.md').write_text(figure_readme, encoding='utf-8')
    from scripts.dashboard import export_handoff_dashboard
    export_handoff_dashboard(output, rows, status)
    sections = [
        ('5.1 Môi trường thực nghiệm', 'Metadata lịch sử ghi PostgreSQL 18.3. Thông tin CPU và logical cores giữa các manifest chưa nhất quán; không suy ra cấu hình máy từ thời gian đo. Xem evidence/environment_historical.json.'),
        ('5.2 Vận hành hệ thống', 'Bộ dữ liệu gồm ba quy mô 50K/200K/500K. Gói có 600 plan lịch sử, 30 trường hợp × 20 lượt. Không có bằng chứng độc lập về 90 warm-up, bất biến database hoặc equivalence đầy đủ; không xem đây là nhật ký vận hành mới.'),
        ('5.3 Kết quả Q1–Q4', 'Median và IQR được tính lại từ Execution Time của raw JSON; Planning Time không được cộng vào Execution Time. Bảng benchmark_summary là nguồn chung cho dashboard và hình thời gian.'),
        ('5.4 So sánh theo quy mô', 'FIG03 mô tả quan hệ thời gian với số bản ghi trong cùng bộ evidence lịch sử. Ba tập có quan hệ prefix; không phải ba mẫu độc lập. Không ngoại suy sang quy mô hoặc phần cứng khác.'),
        ('5.5 Phân tích nguyên nhân', 'Q3 cần so A/B và C/D để xem rewriting, A/C và B/D để xem index. A/D kết hợp hai tác động. Q4 là đối chứng: speedup dưới 1 nghĩa là indexed chậm hơn. FIG06 đếm node scan thực tế, không phải số truy vấn; một plan có thể có nhiều node. Plan hỗ trợ giải thích cơ chế nhưng không tự chứng minh quan hệ nhân quả.'),
        ('5.6 Hạn chế thực nghiệm', 'Trạng thái HISTORICAL. Revision nguồn trong build report là null. Chưa xác minh môi trường, tải nền, cache, autovacuum, fingerprint database hoặc equivalence tại thời điểm đo. Dung lượng index lấy từ summary lịch sử, không suy ra từ EXPLAIN. FIG08 lấy từ build report, không phải lần đo database mới. Chưa có benchmark mới được nghiệm thu.')]
    doc='# Bàn giao Chương 5 — kết quả lịch sử\n\n'+'\n\n'.join('## '+h+'\n\n'+t for h,t in sections)
    doc+='\n\n## Danh mục hình\n\n'
    for i,title in enumerate(titles,1):
        source='evidence/build_report.json' if i==8 else 'evidence/benchmark_raw_plans.zip' if i==6 else 'tables/benchmark_summary.csv'
        doc+=f'- Hình {i}: [{title}](figures/FIG{i:02d}.png), [SVG](figures/FIG{i:02d}.svg). Nguồn: `{source}`. Trạng thái HISTORICAL. '+('Tần suất node scan.' if i==6 else 'NULL / số bản ghi × 100.' if i==8 else 'Speedup = median baseline / median cấu hình.' if i==2 else 'Median của 20 lượt; riêng FIG07 dùng index_bytes lịch sử.')+'\n'
    doc+='\n## Danh mục bảng\n\n'
    for i,p in enumerate(sorted((output/'tables').glob('*.csv')),1):
        doc+=f'- Bảng {i}: [{p.stem}](tables/{p.name}). Đơn vị và nguồn tại bản Markdown tương ứng; kết quả benchmark là HISTORICAL.\n'
    (output/'chapter5_handoff.md').write_text(doc,encoding='utf-8')
    if status == 'LIVE_MEASURED':
        (output/'README.md').write_text('# TV2 — LIVE_MEASURED / NOT_VALIDATED\n\nNguồn: experiment.json, raw plans và catalog validation. QA chưa chạy. FIG08 lấy từ build report. environment_historical.json chỉ là tham chiếu lịch sử; không suy diễn cùng môi trường.\n', encoding='utf-8')
        return
    (output/'README.md').write_text('# Gói TV2 — HISTORICAL / PARTIAL\n\nMở dashboard/index.html trực tiếp; không cần mạng hay API. TV3 dùng chapter5_handoff.md và tables/*.md; PNG 300 DPI, SVG để chỉnh kích thước. Không công bố là benchmark chính thức.\n\nTái tạo từ repository: `python -B -m scripts.package_benchmark`. Raw nguồn không bị thay đổi. Benchmark mới chỉ trên database thử nghiệm độc lập; runner còn cần nghiệm thu hardening trước khi chạy.\n',encoding='utf-8')
