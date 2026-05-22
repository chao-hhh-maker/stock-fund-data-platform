"""
导入所有模型以确保SQLAlchemy关系能正确解析
"""
from app.models.user import User
from app.models.role import Role
from app.models.crawl import CrawlJob, CrawlRun
from app.models.stock_daily import StockDaily
from app.models.fund_nav import FundNav
from app.models.instrument import Instrument

__all__ = ["User", "Role", "CrawlJob", "CrawlRun", "StockDaily", "FundNav", "Instrument"]
