"""
基金净值数据模型
"""
from sqlalchemy import Column, BigInteger, Integer, String, Date, DECIMAL, DateTime, func
from app.core.database import Base


class FundNav(Base):
    """基金净值数据表"""
    __tablename__ = "fund_nav"

    id = Column(BigInteger, primary_key=True, index=True, comment="记录ID")
    code = Column(String(20), nullable=False, index=True, comment="基金代码")
    nav_date = Column(Date, nullable=False, index=True, comment="净值日期")
    unit_nav = Column(DECIMAL(10, 4), comment="单位净值")
    accumulated_nav = Column(DECIMAL(10, 4), comment="累计净值")
    daily_growth = Column(DECIMAL(6, 4), comment="日增长率(%)")
    data_source = Column(String(50), comment="数据来源")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<FundNav(code='{self.code}', date={self.nav_date})>"
