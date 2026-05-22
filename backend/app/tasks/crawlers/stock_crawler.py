"""
股票日线数据采集器
使用 Akshare 获取股票日线数据
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
    standardize_stock_code,
    filter_invalid_records
)

logger = logging.getLogger(__name__)


class StockDailyCrawler:
    """股票日线数据采集器"""
    
    def __init__(self):
        self.source = "akshare"
    
    def fetch_stock_daily(
        self, 
        stock_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取单只股票的日线数据
        
        Args:
            stock_code: 股票代码（6位）
            start_date: 开始日期，格式 YYYYMMDD，默认为最近一年
            end_date: 结束日期，格式 YYYYMMDD，默认为今天
        
        Returns:
            DataFrame 包含股票日线数据
        """
        try:
            # 标准化股票代码
            stock_code = standardize_stock_code(stock_code)
            
            # 设置默认日期范围（最近一年）
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
            logger.info(f"开始采集股票 {stock_code} 的日线数据 ({start_date} 至 {end_date})")
            
            # 使用 akshare 获取股票历史行情数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                logger.warning(f"股票 {stock_code} 没有获取到数据")
                return pd.DataFrame()
            
            logger.info(f"成功获取股票 {stock_code} 的 {len(df)} 条日线数据")
            return df
            
        except Exception as e:
            logger.error(f"采集股票 {stock_code} 日线数据失败: {e}")
            raise
    
    def clean_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗和标准化股票日线数据
        
        Args:
            df: 原始数据框
        
        Returns:
            清洗后的数据框
        """
        if df.empty:
            return df
        
        logger.info("开始清洗股票日线数据")
        
        # 1. 重命名列以匹配数据库字段
        column_mapping = {
            '日期': 'trade_date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change_amount',
            '换手率': 'turnover_rate'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # 2. 过滤无效记录（必需字段）
        required_columns = ['trade_date', 'open', 'high', 'low', 'close']
        df = filter_invalid_records(df, required_columns)
        
        # 3. 处理缺失值
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount', 
                          'change_pct', 'turnover_rate']
        df = handle_missing_values(df, numeric_columns)
        
        # 4. 转换数据类型
        type_mapping = {
            'trade_date': 'datetime64',
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': int,
            'amount': float,
            'change_pct': float,
            'turnover_rate': float
        }
        df = validate_data_types(df, type_mapping)
        
        # 5. 去除重复记录（基于日期）
        df = remove_duplicates(df, subset=['trade_date'])
        
        # 6. 添加元数据字段
        df['data_source'] = self.source
        
        logger.info(f"数据清洗完成，剩余 {len(df)} 条记录")
        return df
    
    def fetch_multiple_stocks(
        self, 
        stock_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的日线数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            字典，key为股票代码，value为DataFrame
        """
        results = {}
        total = len(stock_codes)
        
        for idx, code in enumerate(stock_codes, 1):
            try:
                logger.info(f"进度: [{idx}/{total}] 正在采集股票 {code}")
                df = self.fetch_stock_daily(code, start_date, end_date)
                
                if not df.empty:
                    # 添加股票代码列
                    df['code'] = standardize_stock_code(code)
                    results[code] = df
                else:
                    logger.warning(f"股票 {code} 未获取到数据")
                    
            except Exception as e:
                logger.error(f"采集股票 {code} 失败: {e}")
                # 继续采集下一只股票，不中断整个流程
                continue
        
        logger.info(f"批量采集完成，成功获取 {len(results)}/{total} 只股票的数据")
        return results
    
    def prepare_for_database(self, df: pd.DataFrame, stock_code: str) -> List[Dict[str, Any]]:
        """
        准备数据用于数据库插入
        
        Args:
            df: 清洗后的数据框
            stock_code: 股票代码
        
        Returns:
            字典列表，每个字典代表一行数据
        """
        if df.empty:
            return []
        
        # 确保有 code 列
        if 'code' not in df.columns:
            df['code'] = standardize_stock_code(stock_code)
        
        records = []
        for _, row in df.iterrows():
            record = {
                'code': row['code'],
                'trade_date': row['trade_date'].date() if hasattr(row['trade_date'], 'date') else row['trade_date'],
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else None,
                'amount': float(row['amount']) if pd.notna(row['amount']) else None,
                'change_pct': float(row['change_pct']) if pd.notna(row['change_pct']) else None,
                'turnover_rate': float(row['turnover_rate']) if pd.notna(row['turnover_rate']) else None,
                'data_source': row.get('data_source', self.source)
            }
            records.append(record)
        
        return records
