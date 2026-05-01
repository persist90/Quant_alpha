"""L1 데이터 파이프라인 Prefect 서버 데몬 - 매 거래일 15:40 KST 자동 실행.

Usage:
    poetry run python flows/serve_l1_pipeline.py

기능:
    - 월~금 15:40 KST에 자동 실행
    - KOSDAQ 150 일봉(pykrx) + 4H봉(KIS API) 수집 후 TimescaleDB 적재
    - 완료/실패 시 Slack 알림 (SLACK_WEBHOOK_URL 설정 시)

종료:
    Ctrl+C 또는 프로세스 종료
"""

from quant_alpha.l1_ingestion.market_price.pipeline import market_price_pipeline

if __name__ == "__main__":
    market_price_pipeline.serve(
        name="l1-daily-market-price",
        cron="40 15 * * 1-5",
        timezone="Asia/Seoul",
        description="KOSDAQ 150 일봉(pykrx) + 4H봉(KIS API) 매일 15:40 KST 자동 수집",
    )
