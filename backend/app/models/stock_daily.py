"""
股票日线数据模型
"""
from sqlalchemy import Column, BigInteger, Integer, String, Date, DECIMAL, DateTime, func
from app.core.database import Base


class StockDaily(Base):
    """股票日线数据表"""
    __tablename__ = "stock_daily"

    id = Column(BigInteger, primary_key=True, index=True, comment="记录ID")
    code = Column(String(20), nullable=False, index=True, comment="股票代码")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")
    open = Column(DECIMAL(10, 2), comment="开盘价")
    high = Column(DECIMAL(10, 2), comment="最高价")
    low = Column(DECIMAL(10, 2), comment="最低价")
    close = Column(DECIMAL(10, 2), comment="收盘价")
    volume = Column(BigInteger, comment="成交量(股)")
    amount = Column(DECIMAL(15, 2), comment="成交额(元)")
    change_pct = Column(DECIMAL(6, 2), comment="涨跌幅(%)")
    turnover_rate = Column(DECIMAL(6, 2), comment="换手率(%)")
    data_source = Column(String(50), comment="数据来源")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<StockDaily(code='{self.code}', date={self.trade_date})>"
