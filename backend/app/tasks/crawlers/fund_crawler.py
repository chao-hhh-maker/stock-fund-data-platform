"""
基金净值数据采集器
使用 Akshare 获取基金净值数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from app.tasks.cleaners.data_cleaner import (
    handle_missing_values,
    remove_duplicates,
    validate_data_types,
    filter_invalid_records
)

logger = logging.getLogger(__name__)


class FundNavCrawler:
    """基金净值数据采集器"""
    
    def __init__(self):
        self.source = "akshare"
    
    def fetch_fund_nav(
        self, 
        fund_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取单只基金的净值数据
        
        Args:
            fund_code: 基金代码（6位）
            start_date: 开始日期，格式 YYYY-MM-DD，默认为最近一年
            end_date: 结束日期，格式 YYYY-MM-DD，默认为今天
        
        Returns:
            DataFrame 包含基金净值数据
        """
        try:
            # 设置默认日期范围（最近一年）
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            logger.info(f"开始采集基金 {fund_code} 的净值数据 ({start_date} 至 {end_date})")
            
            # 使用 akshare 获取基金历史净值数据
            df = ak.fund_open_fund_info_em(
                fund=fund_code,
                indicator="单位净值走势"
            )
            
            if df.empty:
                logger.warning(f"基金 {fund_code} 没有获取到数据")
                return pd.DataFrame()
            
            logger.info(f"成功获取基金 {fund_code} 的 {len(df)} 条净值数据")
            return df
            
        except Exception as e:
            logger.error(f"采集基金 {fund_code} 净值数据失败: {e}")
            raise
    
    def clean_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗和标准化基金净值数据
        
        Args:
            df: 原始数据框
        
        Returns:
            清洗后的数据框
        """
        if df.empty:
            return df
        
        logger.info("开始清洗基金净值数据")
        
        # 1. 重命名列以匹配数据库字段
        column_mapping = {
            '净值日期': 'nav_date',
            '单位净值': 'unit_nav',
            '累计净值': 'accumulated_nav',
            '日增长率': 'daily_growth'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # 2. 过滤无效记录（必需字段）
        required_columns = ['nav_date', 'unit_nav']
        df = filter_invalid_records(df, required_columns)
        
        # 3. 处理缺失值
        numeric_columns = ['unit_nav', 'accumulated_nav', 'daily_growth']
        df = handle_missing_values(df, numeric_columns)
        
        # 4. 转换数据类型
        type_mapping = {
            'nav_date': 'datetime64',
            'unit_nav': float,
            'accumulated_nav': float,
            'daily_growth': float
        }
        df = validate_data_types(df, type_mapping)
        
        # 5. 去除重复记录（基于日期）
        df = remove_duplicates(df, subset=['nav_date'])
        
        # 6. 添加元数据字段
        df['data_source'] = self.source
        
        logger.info(f"数据清洗完成，剩余 {len(df)} 条记录")
        return df
    
    def fetch_multiple_funds(
        self, 
        fund_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只基金的净值数据
        
        Args:
            fund_codes: 基金代码列表
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            字典，key为基金代码，value为DataFrame
        """
        results = {}
        total = len(fund_codes)
        
        for idx, code in enumerate(fund_codes, 1):
            try:
                logger.info(f"进度: [{idx}/{total}] 正在采集基金 {code}")
                df = self.fetch_fund_nav(code, start_date, end_date)
                
                if not df.empty:
                    # 添加基金代码列
                    df['code'] = code
                    results[code] = df
                else:
                    logger.warning(f"基金 {code} 未获取到数据")
                    
            except Exception as e:
                logger.error(f"采集基金 {code} 失败: {e}")
                # 继续采集下一只基金，不中断整个流程
                continue
        
        logger.info(f"批量采集完成，成功获取 {len(results)}/{total} 只基金的数据")
        return results
    
    def prepare_for_database(self, df: pd.DataFrame, fund_code: str) -> List[Dict[str, Any]]:
        """
        准备数据用于数据库插入
        
        Args:
            df: 清洗后的数据框
            fund_code: 基金代码
        
        Returns:
            字典列表，每个字典代表一行数据
        """
        if df.empty:
            return []
        
        # 确保有 code 列
        if 'code' not in df.columns:
            df['code'] = fund_code
        
        records = []
        for _, row in df.iterrows():
            record = {
                'code': row['code'],
                'nav_date': row['nav_date'].date() if hasattr(row['nav_date'], 'date') else row['nav_date'],
                'unit_nav': float(row['unit_nav']) if pd.notna(row['unit_nav']) else None,
                'accumulated_nav': float(row['accumulated_nav']) if pd.notna(row['accumulated_nav']) else None,
                'daily_growth': float(row['daily_growth']) if pd.notna(row['daily_growth']) else None,
                'data_source': row.get('data_source', self.source)
            }
            records.append(record)
        
        return records
