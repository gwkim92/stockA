"""Package original application screenshots without modifying their pixels."""
from pathlib import Path
import html, json, zipfile
root = Path('output/playwright/research-workspace-redesign-20260911')
labels = [('home','오늘 살펴볼 것','/'),('company','기업 핵심 논리','/stocks/NVDA'),('financials','재무 비교','/stocks/NVDA?view=company-analysis'),('news','뉴스 목록과 해석','/intelligence'),('source','원천 대조 패널','/intelligence'),('holdings','보유 비교','/portfolio/coverage'),('fund','ETF 구성과 비용','/stocks/SPY?view=company-analysis')]
figures=[]
for key,title,route in labels:
 for size,caption in [('desktop','1440 × 900'),('mobile','390 × 844')]:
  file=f'{key}-{size}.png'
  figures.append(f'<figure data-size="{size}"><figcaption><strong>{title}</strong><span>{caption}</span></figcaption><a href="{file}" target="_blank"><img src="{file}" alt="{title} {caption} 실제 화면" loading="lazy"></a><a class="open" href="http://127.0.0.1:13321{html.escape(route,quote=True)}">작동하는 화면 열기 →</a></figure>')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>stockA · 새 화면 캡처</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f5f0;color:#26313b;font:15px/1.7 -apple-system,"Apple SD Gothic Neo",sans-serif}main{max-width:1500px;padding:36px;margin:auto}h1{font-size:28px;margin:4px 0}p{color:#626e74}nav{display:flex;gap:8px;margin:22px 0}button{padding:10px 16px;border:1px solid #b9c3c0;border-radius:4px;background:#fffefa;color:#245d82;cursor:pointer}button[aria-pressed=true]{background:#245d82;color:white}.grid{display:grid;grid-template-columns:1fr 1fr;gap:28px}figure{margin:0;min-width:0;border-top:1px solid #b9c3c0;padding-top:14px}figcaption{display:flex;justify-content:space-between;margin-bottom:12px}figcaption span{color:#626e74;font-size:12px}img{display:block;width:100%;border:1px solid #dbe0dc}figure[data-size=mobile] img{max-width:390px;margin:auto}a{color:#245d82;text-decoration:none}.open{display:inline-block;padding:12px 0;font-size:13px}[hidden]{display:none!important}@media(max-width:800px){main{padding:20px}.grid{grid-template-columns:1fr}}
</style><main><span>STOCKA / RESEARCH WORKSPACE</span><h1>새 화면, 실제 데이터</h1><p>2026-09-11 · 운영 자료를 읽는 로컬 빌드의 캡처입니다. 원천 발췌가 없는 문서는 요약만 표시합니다. 운영 서버에는 아직 배포하지 않았습니다.</p><nav aria-label="캡처 크기"><button type="button" data-filter="desktop" aria-pressed="true">데스크톱</button><button type="button" data-filter="mobile" aria-pressed="false">모바일</button><button type="button" data-filter="all" aria-pressed="false">모두</button></nav><div class="grid">'''+''.join(figures)+'''</div><p><a href="stockA-redesign-evidence.zip">캡처와 검증 기록 내려받기</a></p></main><script>function show(value){document.querySelectorAll('figure').forEach(el=>el.hidden=value!=='all'&&el.dataset.size!==value);document.querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.filter===value)))}document.querySelectorAll('button').forEach(el=>el.onclick=()=>show(el.dataset.filter));show('desktop')</script></html>'''
(root/'index.html').write_text(page)
with zipfile.ZipFile(root/'stockA-redesign-evidence.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for p in sorted(root.iterdir()):
  if p.suffix in ['.png','.json','.html'] or p.name in ['models-final-log.txt','table-scroll-log.txt']:
   archive.write(p,p.name)
print('gallery and archive ready')
