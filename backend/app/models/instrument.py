"""
金融工具模型（股票/基金基本信息）
"""
from sqlalchemy import Column, Integer, String, Date, Enum, DateTime, func
from app.core.database import Base


class Instrument(Base):
    """金融工具表"""
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True, comment="工具ID")
    code = Column(String(20), nullable=False, index=True, comment="证券代码")
    name = Column(String(100), nullable=False, comment="证券名称")
    type = Column(Enum('stock', 'fund'), nullable=False, comment="类型: stock-股票, fund-基金")
    market = Column(String(20), comment="市场: SH-上海, SZ-深圳, BJ-北京")
    industry = Column(String(50), comment="行业分类")
    list_date = Column(Date, comment="上市日期")
    status = Column(Enum('active', 'delisted'), default='active', comment="状态")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Instrument(code='{self.code}', name='{self.name}', type='{self.type}')>"
