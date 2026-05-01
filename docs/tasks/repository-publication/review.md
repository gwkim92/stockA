# Review Notes

## Scope Review

- 작업 범위는 public repository initial publication과 branch strategy 문서화로 제한한다.
- GitHub branch protection UI, CI workflow, secret scanning service 설정은 이번 범위 밖이다.

## Verification Evidence

- `ssh-keygen -lf /Users/woody/.ssh/id_ed25519_pusan.pub`: `SHA256:eoQlrg9nUtVYZ3/8w+SIsrwqktOrS0/YIgrRZp4a1Qk`
- `git ls-remote git@github.com:gwkim92/stockA.git`: 통과, initial push 전 출력 없음
- `ssh -i /Users/woody/.ssh/id_ed25519_pusan -o IdentitiesOnly=yes -o BatchMode=yes -T git@github.com`: GitHub authentication success message 확인
- staged private/generated file check: 출력 없음
- secret pattern scan excluding generated/docs command examples: 출력 없음
- `git commit -m "chore: publish initial stockanalysis workspace"`: `72973b7`
- `git push -u origin main`: 통과
- `git push -u origin develop`: 통과

## Residual Risks

- `.env.example`에는 placeholder credential names가 포함되어 있으나 실제 secret은 아니다.
- script 내부 `POSTGRES_PASSWORD=postgres`는 Docker verification default로만 사용된다.
- GitHub branch protection은 별도 GitHub settings 작업이 필요하다.
