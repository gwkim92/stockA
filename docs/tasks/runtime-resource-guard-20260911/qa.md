# 검증

- build guard 7개 통과: live/staging/정규화 경로, 다른 EC2 checkout 차단, 개발·GitHub runner·Docker build 경로 허용.
- 활성화 스크립트 Python 문법, git diff 검사 통과.
- 로컬 실제 npm build와 타입 검사 통과. build가 새 보호 진입점을 거쳐 정상 완료됐다. CI 검증은 PR에서 진행한다.
- 서버: SSH banner exchange timeout 재확인. AWS Chrome 콘솔 로그아웃 상태, 개인 계정 로그인 요청 중. 복구/운영 활성화/자원 측정 미완료.
