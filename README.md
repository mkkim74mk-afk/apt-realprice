# 대치동 아파트 실거래 — 매달 자동 갱신 페이지

매달 30일에 GitHub가 국토부 실거래(매매·전세)를 알아서 받아와
휴대폰에서 열어보는 카드 페이지를 자동으로 갱신합니다.

대상: 서울 강남구 대치동 — 래미안대치팰리스 / 대치르엘 / 동부센트레빌 / 대치아이파크

---

## 들어 있는 파일
- `fetch.py` — 국토부 API에서 직전 2개월 실거래를 받아 `data.json`을 만드는 스크립트
- `index.html` — 휴대폰에서 보는 카드 페이지 (data.json을 읽어 표시)
- `.github/workflows/update.yml` — 매달 30일 자동 실행 설정
- `data.json` — (자동 생성됨. 지금은 샘플이 들어 있음)

---

## 처음 한 번만 하는 설치 (약 20~30분)

### 1. 국토부 API 키 발급 (무료)
1. https://www.data.go.kr 회원가입 후 로그인
2. **"국토교통부 아파트 매매 실거래가 자료"** 검색 → **활용신청**
3. **"국토교통부 아파트 전월세 실거래가 자료"** 도 똑같이 **활용신청**
   - 시스템유형: 일반 / 활용목적: 웹 사이트 개발 등으로 신청 (자동 승인)
4. 마이페이지 → **일반 인증키(Decoding)** 복사해 둡니다
   - ※ 신청 후 실제 호출까지 보통 1~2시간 걸립니다.

### 2. GitHub 저장소 만들기
1. https://github.com 가입 후 로그인
2. 우측 상단 **＋ → New repository**
3. 이름 자유(예: `daechi-apt`), **Public** 선택 → **Create repository**

### 3. 파일 올리기
- `fetch.py`, `index.html` → **Add file → Upload files** 로 끌어다 올리기
- 워크플로 파일은 숨김폴더라 업로드가 까다로우니 **새로 만들기**로:
  **Add file → Create new file** → 파일명 칸에
  `.github/workflows/update.yml` 입력 (폴더가 자동 생성됩니다)
  → `update.yml` 내용 붙여넣기 → Commit

### 4. API 키를 비밀값으로 등록
**Settings → Secrets and variables → Actions → New repository secret**
- Name: `MOLIT_KEY`
- Secret: 1번에서 복사한 **Decoding 키** 붙여넣기 → Add secret

### 5. 첫 실행
**Actions 탭 → "실거래 자동 갱신" → Run workflow**
- 1~2분 뒤 `data.json`이 실제 거래로 갱신됩니다.

### 6. 페이지 켜기 (GitHub Pages)
**Settings → Pages → Source: Deploy from a branch → Branch: main / (root) → Save**
- 1~2분 뒤 주소가 생깁니다: `https://본인아이디.github.io/저장소이름/`

### 7. 휴대폰에 추가
- 위 주소를 휴대폰 브라우저로 열고 **홈 화면에 추가**(북마크).
- 이후 매달 30일(2월은 28일)에 자동으로 최신 2개월 거래로 갱신됩니다.

---

## 알아두면 좋은 점
- **평형**은 전용면적 ÷ 0.74(전용률 가정) ÷ 3.3058 로 계산한 **추정치**입니다.
  단지별로 정확히 맞추려면 `fetch.py`의 `EFF` 값을 조정하세요.
- **단지 추가/변경**은 `fetch.py` 위쪽 `TARGETS` 목록만 고치면 됩니다.
- **엔드포인트 오류**가 나면, 활용신청한 API 상세페이지의 엔드포인트 주소를
  `fetch.py`의 `TRADE_URL` / `RENT_URL` 과 비교해 다르면 교체하세요.
- **SERVICE_KEY 오류**가 나면 Encoding/Decoding 키 중 다른 쪽으로 바꿔 보세요(Decoding 권장).
- GitHub의 예약 실행은 저장소가 오래 잠잠하면 멈출 수 있습니다.
  멈추면 Actions에서 **Run workflow**를 한 번 눌러 다시 깨우면 됩니다.
