"""교보 템플릿 문서 요약 분석 (UTF-8 출력 전용)"""
import json
import os

ANALYSIS_PATH = r"c:\Users\aiueo\projects\quant-alpha\kyobo_template\_analysis_result.json"
OUTPUT_PATH = r"c:\Users\aiueo\projects\quant-alpha\kyobo_template\_summary.md"

with open(ANALYSIS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []

for doc in data:
    lines.append(f"## {doc['filename']}")
    lines.append(f"- **총 문단**: {doc['total_paragraphs']}")
    lines.append(f"- **테이블**: {len(doc['tables'])}개")
    lines.append(f"- **이미지**: {doc['images']}개")
    lines.append(f"- **폰트**: {', '.join(doc['fonts_used'])}")
    lines.append(f"- **색상(RGB)**: {', '.join(doc['colors_used'])}")
    
    lines.append(f"\n### 스타일 분포")
    for style, count in sorted(doc['styles_used'].items(), key=lambda x: -x[1]):
        lines.append(f"- {style}: {count}회")
    
    lines.append(f"\n### 헤딩 구조")
    for h in doc['heading_structure']:
        lines.append(f"- [{h['level']}] {h['text']}")
    if not doc['heading_structure']:
        lines.append("- (Word 기본 Heading 스타일 미사용 - Normal/List Paragraph로 구조화)")
    
    lines.append(f"\n### 주요 내용 (처음 15개 문단)")
    for s in doc['sections'][:15]:
        text = s['text'][:120].replace('\n', ' ')
        lines.append(f"- [{s['style']}] {text}")
    
    lines.append(f"\n### 테이블 요약")
    for t in doc['tables'][:8]:
        header_text = ' | '.join(h[:30] for h in t['header_row'])
        lines.append(f"- Table {t['table_index']}: {t['rows']}행 x {t['cols']}열 - 헤더: [{header_text}]")
    if len(doc['tables']) > 8:
        lines.append(f"- ... 외 {len(doc['tables'])-8}개 테이블")
    
    lines.append(f"\n### 페이지 설정")
    for p in doc['page_settings']:
        # EMU to cm conversion (1 cm = 360000 EMU)
        w_cm = int(p['page_width']) / 360000
        h_cm = int(p['page_height']) / 360000
        lm = int(p['left_margin']) / 360000
        rm = int(p['right_margin']) / 360000
        tm = int(p['top_margin']) / 360000
        bm = int(p['bottom_margin']) / 360000
        lines.append(f"- 페이지: {w_cm:.1f}cm x {h_cm:.1f}cm")
        lines.append(f"- 여백: 좌{lm:.1f} 우{rm:.1f} 상{tm:.1f} 하{bm:.1f} cm")
    
    lines.append("\n---\n")

# 공통 패턴 분석
lines.append("## 공통 패턴 분석\n")

all_fonts = set()
all_colors = set()
all_styles = {}
total_tables = 0
total_images = 0

for doc in data:
    all_fonts.update(doc['fonts_used'])
    all_colors.update(doc['colors_used'])
    total_tables += len(doc['tables'])
    total_images += doc['images']
    for s, c in doc['styles_used'].items():
        all_styles[s] = all_styles.get(s, 0) + c

lines.append(f"### 전체 통계")
lines.append(f"- 문서 수: {len(data)}")
lines.append(f"- 총 테이블: {total_tables}개")
lines.append(f"- 총 이미지: {total_images}개")

lines.append(f"\n### 공통 폰트")
for f in sorted(all_fonts):
    lines.append(f"- {f}")

lines.append(f"\n### 공통 색상")
for c in sorted(all_colors):
    lines.append(f"- #{c}")

lines.append(f"\n### 공통 스타일")
for s, c in sorted(all_styles.items(), key=lambda x: -x[1]):
    lines.append(f"- {s}: {c}회")

content = '\n'.join(lines)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Summary saved to: {OUTPUT_PATH}")
print(f"\nDone. {len(data)} documents analyzed.")
