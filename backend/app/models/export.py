"""
数据导出模型
"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ExportRecord(Base):
    """数据导出记录表"""
    __tablename__ = "export_records"

    id = Column(BigInteger, primary_key=True, index=True, comment="导出记录ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    export_type = Column(Enum('stock_daily', 'fund_nav', 'instrument'), nullable=False, comment="导出类型")
    query_params = Column(Text, comment="查询参数(JSON格式)")
    file_path = Column(String(500), comment="文件路径")
    file_format = Column(Enum('csv', 'excel', 'parquet'), default='csv', comment="文件格式")
    record_count = Column(Integer, default=0, comment="记录数量")
    file_size = Column(BigInteger, comment="文件大小(字节)")
    status = Column(Enum('pending', 'processing', 'completed', 'failed'), default='pending', comment="导出状态")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    completed_at = Column(DateTime, comment="完成时间")

    # 关系
    user = relationship("User", backref="export_records")

    def __repr__(self):
        return f"<ExportRecord(id={self.id}, type='{self.export_type}', status='{self.status}')>"
