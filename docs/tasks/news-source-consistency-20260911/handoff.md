# 뉴스 식별자 충돌 재발 방지와 문서 격리

2026-09-11. 로컬 구현과 관련 검증을 완료했으며 운영 적용을 준비 중이다.

근본 원인: Yahoo RSS의 `?src=A00220&yptr=yahoo`가 article GUID로 처리되어 여러 기사 제목/원문이 같은 source-document-22/event-19를 덮어썼다. 기존 번역과 AAPL/테마 연결이 유지돼 원천이 섞였다. 실제 feed와 5월 fixture의 같은 hash로 확인했다.

구현: 잘못된 GUID만 기사 URL로 식별, 격리 문서 덮어쓰기 차단, fingerprint와 기록 보존을 갖춘 격리 service, 원천 상세/빠른 패널/기업 검토 원천의 불일치 표시 및 혼합 번역/발췌 표시 제외. 운영 대상은 문서 22, 이벤트 19, 종목 연결 1, 테마 연결 6이다.

운영 준비: activate_runtime.py는 기존 검증된 Linux artifact 배포 절차를 별도 task 경로에서 실행한다. 개인 AWS identity, develop와 artifact 코드 동일성, dependency/schema 불변, 환경/model 불변, 서비스 및 타이머 복원, 이전 소스/빌드 백업을 검사한다. repair_runtime.py는 운영 preview 지문 일치와 activation receipt를 요구하며 문서 22만 격리한다. 시작 receipt가 있으면 자동 재실행하지 않는다.

아직 운영 적용/교정/Chrome 검증 완료로 표현하지 않는다. 완료 후 증거를 이 문서에 갱신한다. 다른 task의 기존 사용자 변경은 건드리지 않는다.
