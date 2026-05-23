# Review Notes

- 이 작업은 표시 계층과 DTO provenance만 바꾼다.
- 추천 점수 weight, 추천 산식, 데이터 수집 cadence는 변경하지 않는다.
- Local verification:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`: pass
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: pass
  - `cd apps/web && npm run typecheck`: pass
  - `cd apps/web && npm run build`: pass
  - `git diff --check`: pass
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-recommendation-cycle-waterfall`: pass
- EC2 verification:
  - Deployed `57913b9`.
  - `npm --prefix apps/web run build`: pass on EC2.
  - `stockanalysis-frontend-api.service`: active.
  - `stockanalysis-web.service`: active.
  - `GET http://127.0.0.1:13000/recommendations`: 200.
  - `GET http://127.0.0.1:13000/recommendations/recommendation-135`: 200.
  - `GET http://127.0.0.1:13000/recommendations/recommendation-133`: 200.
  - Rendered HTML contains cycle waterfall labels and no `Server Components render`, `digest`, or `FrontendApiError`.
