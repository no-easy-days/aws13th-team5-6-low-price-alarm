# aws13th-team5-6-low-price-alarm

업비트 시세 수집, 히스토리/통계 제공, 가격 알람 트리거를 처리하는 FastAPI 데모입니다.

## 구성 요약
- **백엔드**: FastAPI + SQLAlchemy + MySQL
- **프론트**: `/static` 대시보드 (그래프/통계/알람)
- **수집기**: 일정 주기로 업비트 API 호출

## 프로젝트 구조
- `routers/`
  - `routers/coins.py`: 코인/히스토리/통계 조회
  - `routers/alerts.py`: 알람 생성/조회 + WebSocket
- `services/`
  - `services/collector.py`: 수집 스레드(업비트 호출, 히스토리 저장, 통계/알람 갱신)
- `database.py`: DB 연결/세션
- `models.py`: SQLAlchemy 모델
- `schemas.py`: Pydantic 스키마
- `crud.py`: DB 접근 로직
- `main.py`: FastAPI 엔트리포인트

## 데이터 흐름
1. 수집 스레드가 업비트 API 호출
2. `coin_history`에 가격 히스토리 저장
3. `daily_coin_statistics`에 일별 통계 upsert
4. 알람 조건 만족 시 WebSocket으로 트리거 이벤트 전송

## 주요 테이블
- `coins`: 코인 마스터 (market, 이름)
- `coin_history`: 시계열 가격 기록
- `daily_coin_statistics`: 일별 통계
- `alerts`: 알람 조건/상태

## 실행 방법
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## 환경 변수 예시
```
MYSQL_HOST=...
MYSQL_PORT=33306
MYSQL_DATABASE=team5_db
MYSQL_USER=team5
MYSQL_PASSWORD=...
COLLECT_INTERVAL_SECONDS=60
```

## 데모 체크리스트
1. `/coins` 응답 확인
2. 히스토리/통계 그래프 렌더링 확인
3. 알람 생성 및 트리거 확인
