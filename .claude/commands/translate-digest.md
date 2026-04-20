---
description: 최신 논문 다이제스트의 영문 초록을 한국어로 번역해 커밋·푸시
allowed-tools: Read, Edit, Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(ls:*), Glob
---

# /translate-digest

오늘자 (또는 가장 최근) 일일 논문 다이제스트의 영문 초록을 비전공자도 이해할 수 있는 한국어로 번역하여 같은 파일에 채워 넣고 커밋·푸시합니다.

## 작업 절차

1. **대상 파일 결정**
   - `papers/` 디렉토리에서 가장 최근 날짜 파일 (`YYYY-MM-DD.md`) 을 찾는다
   - 같은 내용으로 `papers/latest.md` 도 함께 갱신한다

2. **각 논문 항목 번역**
   - 파일 안의 모든 `### {제목}` 블록에 대해:
     - `**Abstract (EN)**: ...` 의 영문 초록을 읽는다
     - `**한국어 요약**: _대기 중 ..._` 줄을 다음 형식의 한국어 요약으로 교체한다:
       - **3-4 문장**, 비전공자가 이해 가능한 표현
       - **순서**: 배경 → 방법 → 주요 발견 → 의의
       - **사실 위주**, 수식어/감탄형 배제 ("매우", "획기적인" 등 금지)
       - 전문 용어는 1회 한국어로 풀어 쓴 뒤 괄호로 영문 병기 (예: "유전체 광범위 연관성 분석(GWAS)")
       - 초록이 `(초록이 제공되지 않았습니다.)` 인 경우 한국어 요약도 `_원문 초록 없음 — 번역 생략._` 로 둔다
       - "Guide for Authors", "Table of Contents", "Subscribers Page", "Editorial Board" 등 비논문 항목은 `_논문 외 항목 — 번역 생략._` 로 둔다

3. **커밋 & 푸시**
   - `git status` 로 변경 확인
   - 변경이 있으면:
     ```
     git add papers/
     git commit -m "docs: translate digest YYYY-MM-DD to Korean"
     git push
     ```
   - 변경 없으면 "이미 번역됨 — 건너뜀" 을 출력하고 종료

## 출력
- 처리한 파일 경로
- 번역한 논문 수 / 건너뛴 논문 수
- 커밋 SHA (있을 경우)
