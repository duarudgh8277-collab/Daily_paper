# Daily Paper Digest

지정된 저널 목록의 최신 논문을 매일 오전 9시(KST) 자동 수집하고, 한국어 요약은 Claude Code 에서 슬래시 명령으로 채워 넣는 워크플로우입니다. **외부 LLM API 키가 필요 없습니다.**

## 동작 방식

1. **자동 수집 (매일 09:00 KST)**: GitHub Actions 가 `journals.yml` 의 RSS 피드에서 최근 논문을 모아 `papers/YYYY-MM-DD.md` 와 `papers/latest.md` 를 커밋합니다. 이 단계의 "**한국어 요약**" 항목은 비어 있고 영문 초록만 들어갑니다.
2. **수동 한국어 요약**: 사용자가 Claude Code 에서 `/translate-digest` 를 실행하면 Claude 가 최신 다이제스트를 읽어 각 논문의 영문 초록을 비전공자용 3-4문장 한국어로 채우고 커밋·푸시합니다.

## 수집 저널 (22개)

Nature, Science, Cell, Nature Genetics, Nature Neuroscience, Nature Machine Intelligence,
Genome Biology, Genome Medicine, Nature Computational Science, Nature Methods,
American Journal of Human Genetics, Cell Genomics, Nature Human Behaviour, Neuron,
Molecular Psychiatry, Biological Psychiatry, Molecular Systems Biology,
Nature Communications, Nucleic Acids Research, Briefings in Bioinformatics,
Bioinformatics, Genome Research

## 사용 흐름

### 1. 자동 수집 (사용자 작업 없음)
매일 00:00 UTC (09:00 KST) 에 GitHub Actions 가 실행되어 영문 다이제스트를 만듭니다.

수동 트리거가 필요하면: 저장소 **Actions → Daily paper digest → Run workflow**.

### 2. 한국어 요약 (Claude Code)
이 저장소에서 Claude Code 를 열고:

```
/translate-digest
```

또는 더 길게:

```
오늘자 다이제스트를 한국어로 정리해줘.
- papers/latest.md 를 읽어 각 논문의 "한국어 요약" 항목을 채워
- 비전공자도 이해할 3-4문장 (배경 → 방법 → 발견 → 의의), 사실 위주, 수식어 배제
- 같은 파일과 papers/YYYY-MM-DD.md 둘 다 갱신, 커밋 후 push
```

## 로컬 실행 (수집만)

```bash
pip install -r requirements.txt
python fetch_papers.py
```

## 커스터마이징

- 저널 추가/제거: `journals.yml` 의 `journals` 리스트 수정
- 저널당 논문 수: `per_journal_limit`
- 수집 기간(일): `lookback_days`
- 스케줄 변경: `.github/workflows/daily.yml` 의 cron 수정
- 한국어 요약 스타일 변경: `.claude/commands/translate-digest.md` 수정

## 출력 형식

`papers/YYYY-MM-DD.md` 파일에 저널별로 그룹핑:

- 제목, 저자, 게재일, 원문 링크
- **Abstract (EN)**: RSS 원본 영문 초록
- **한국어 요약**: `/translate-digest` 실행 후 채워짐

`papers/latest.md` 는 항상 최신 다이제스트를 가리킵니다.
