# Daily Paper Digest

지정된 저널 목록의 최신 논문을 매일 오전 9시(KST) 자동 수집하여 한국어로 요약합니다.

## 동작 방식

1. GitHub Actions가 매일 00:00 UTC (09:00 KST) 에 트리거
2. `journals.yml` 의 RSS 피드에서 최근 논문 수집 (기본 2일 이내, 저널당 최대 5편)
3. `ANTHROPIC_API_KEY` 가 설정되어 있으면 Claude Haiku 로 초록을 비전공자용 3-4문장 한국어 요약으로 변환
4. `papers/YYYY-MM-DD.md` 와 `papers/latest.md` 를 저장소에 커밋

## 수집 저널 (22개)

Nature, Science, Cell, Nature Genetics, Nature Neuroscience, Nature Machine Intelligence,
Genome Biology, Genome Medicine, Nature Computational Science, Nature Methods,
American Journal of Human Genetics, Cell Genomics, Nature Human Behaviour, Neuron,
Molecular Psychiatry, Biological Psychiatry, Molecular Systems Biology,
Nature Communications, Nucleic Acids Research, Briefings in Bioinformatics,
Bioinformatics, Genome Research

## 설정

### 1. ANTHROPIC_API_KEY 시크릿 등록 (권장)

저장소 Settings → Secrets and variables → Actions → New repository secret
- Name: `ANTHROPIC_API_KEY`
- Value: `sk-ant-...`

미설정 시 RSS 원본 초록이 그대로 들어갑니다.

### 2. 수동 실행

Actions 탭 → **Daily paper digest** → **Run workflow**

### 3. 로컬 실행

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # optional
python fetch_papers.py
```

## 커스터마이징

- 저널 추가/제거: `journals.yml` 의 `journals` 리스트 수정
- 저널당 논문 수: `per_journal_limit`
- 수집 기간(일): `lookback_days`
- 스케줄 변경: `.github/workflows/daily.yml` 의 cron 수정

## 출력 형식

`papers/YYYY-MM-DD.md` 파일에 저널별로 그룹핑된 다이제스트 생성:

- 제목, 저자, 게재일, 원문 링크
- 한국어 요약 (배경 → 방법 → 발견 → 의의)

`papers/latest.md` 는 항상 최신 다이제스트를 가리킵니다.
