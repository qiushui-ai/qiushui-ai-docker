import logging

from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from qiushuiai.core.config import settings
from qiushuiai.core.db import engine

logger = logging.getLogger(__name__)

max_tries = settings.DB_CONNECT_MAX_TRIES
wait_seconds = settings.DB_CONNECT_WAIT_SECONDS


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    """
    等待数据库服务就绪并验证连接
    
    符合 FastAPI 官方模板标准：
    - 只等待数据库服务启动
    - 验证数据库连接可用
    - 不创建数据库（需要提前创建）
    - 不创建表结构（由 Alembic 管理）
    """
    try:
        # 验证数据库连接
        with Session(db_engine) as session:
            # 简单的连接测试，确保数据库服务已就绪
            session.exec(select(1))
        logger.info("✅ 数据库连接成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise e


def main() -> None:
    logger.info("Initializing service")
    init(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()