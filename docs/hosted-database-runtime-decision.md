# Hosted Database Runtime Decision

생성일: 2026-05-20

## 결론

현재 무료 조건에서 가장 현실적인 다음 경로는 **Supabase Free Postgres를 hosted DB 후보로 준비하고, 이후 GitHub Actions scheduled workflow가 `stockanalysis-operations` worker를 실행**하는 방식이다.

단, 이 작업에서는 Supabase 프로젝트를 만들지 않는다. DB URL/비밀번호도 저장하지 않는다.

## 왜 local-only로는 외부 scheduler가 안 되는가

GitHub Actions나 managed scheduler는 GitHub/클라우드 쪽에서 실행된다. 내 Mac의 `127.0.0.1` Postgres는 외부에서 접근할 수 없다.

따라서 외부 scheduler를 쓰려면 최소 하나가 필요하다.

- hosted Postgres
- 이미 보유한 VPS/NAS 같은 상시 실행 host
- local-only runner를 유지한다는 명시적 결정

## 무료 후보 판단

- Supabase Free: 500MB database size, dedicated Postgres, 2 active free projects, inactivity pause가 있다. MVP hosted DB 후보로 적합하지만 production-grade backup/availability는 아니다.
- Render Free Postgres: 1GB지만 30일 후 만료되므로 지속 운영 DB로 부적합하다.
- Railway Free: 크레딧 기반이므로 “돈 없음” 조건에서 예산 초과/중단 리스크가 있다.
- Existing host: 이미 가진 서버가 있다면 비용 추가 없이 가장 안정적일 수 있다. 현재는 제공되지 않았다.

## 다음 작업

`supabase-free-postgres-setup-packet`

이 작업에서 사용자가 Supabase에서 무엇을 만들고, 어떤 값을 repo 밖 env/GitHub secrets에 넣어야 하는지 정확히 정리한다.

## 공식 근거

- Supabase Free plan: <https://supabase.com/pricing>
- Supabase billing/free projects: <https://supabase.com/docs/guides/platform/billing-on-supabase>
- Supabase database size behavior: <https://supabase.com/docs/guides/platform/database-size>
- Render Free Postgres limits: <https://render.com/free>
- GitHub Actions billing/free public repositories: <https://docs.github.com/actions/administering-github-actions/usage-limits-billing-and-administration>
