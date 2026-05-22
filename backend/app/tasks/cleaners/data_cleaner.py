"""
数据清洗工具
提供缺失值处理、异常值处理等功能
"""
import pandas as pd
import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def handle_missing_values(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    处理缺失值
    
    Args:
        df: 数据框
        columns: 需要处理的列，None表示所有数值列
    
    Returns:
        处理后的数据框
    """
    df_cleaned = df.copy()
    
    if columns is None:
        # 默认处理所有数值列
        numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns
        columns = numeric_cols.tolist()
    
    for col in columns:
        if col not in df_cleaned.columns:
            continue
        
        # 统计缺失值数量
        missing_count = df_cleaned[col].isnull().sum()
        if missing_count > 0:
            logger.info(f"列 {col} 有 {missing_count} 个缺失值")
            
            # 对于数值列，使用中位数填充
            if df_cleaned[col].dtype in [np.float64, np.int64]:
                median_val = df_cleaned[col].median()
                df_cleaned[col].fillna(median_val, inplace=True)
                logger.info(f"列 {col} 使用中位数 {median_val} 填充缺失值")
    
    return df_cleaned


def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
    """
    去除重复记录
    
    Args:
        df: 数据框
        subset: 用于判断重复的列，None表示所有列
    
    Returns:
        去重后的数据框
    """
    original_count = len(df)
    df_cleaned = df.drop_duplicates(subset=subset)
    removed_count = original_count - len(df_cleaned)
    
    if removed_count > 0:
        logger.info(f"去除 {removed_count} 条重复记录")
    
    return df_cleaned


def validate_data_types(df: pd.DataFrame, type_mapping: dict) -> pd.DataFrame:
    """
    验证和转换数据类型
    
    Args:
        df: 数据框
        type_mapping: 列名到目标类型的映射，如 {'code': str, 'date': 'datetime64'}
    
    Returns:
        类型转换后的数据框
    """
    df_converted = df.copy()
    
    for col, target_type in type_mapping.items():
        if col not in df_converted.columns:
            continue
        
        try:
            if target_type == 'datetime64':
                df_converted[col] = pd.to_datetime(df_converted[col])
            elif target_type == str:
                df_converted[col] = df_converted[col].astype(str)
            elif target_type in [int, float]:
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
            else:
                df_converted[col] = df_converted[col].astype(target_type)
                
            logger.info(f"列 {col} 成功转换为 {target_type}")
        except Exception as e:
            logger.warning(f"列 {col} 类型转换失败: {e}")
    
    return df_converted


def standardize_stock_code(code: str) -> str:
    """
    标准化股票代码
    
    Args:
        code: 原始股票代码
    
    Returns:
        标准化后的代码（6位数字）
    """
    if not code:
        return code
    
    # 移除空格和特殊字符
    code = str(code).strip().replace('.', '').replace('-', '')
    
    # 确保是6位数字
    if len(code) == 6 and code.isdigit():
        return code
    
    # 如果不足6位，前面补0
    if code.isdigit():
        return code.zfill(6)
    
    logger.warning(f"无法标准化股票代码: {code}")
    return code


def filter_invalid_records(df: pd.DataFrame, required_columns: List[str]) -> pd.DataFrame:
    """
    过滤无效记录（关键字段为空的记录）
    
    Args:
        df: 数据框
        required_columns: 必需的列
    
    Returns:
        过滤后的数据框
    """
    original_count = len(df)
    
    # 删除关键字段为空的记录
    df_filtered = df.dropna(subset=required_columns)
    
    removed_count = original_count - len(df_filtered)
    if removed_count > 0:
        logger.info(f"过滤掉 {removed_count} 条无效记录（关键字段缺失）")
    
    return df_filtered
