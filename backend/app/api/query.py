"""受控 SQL 查询路由（模块4：通用 SQL 查询接口）。

安全设计：
- 仅管理员可用。
- 只允许单条 SELECT 语句；禁止分号多语句、DML/DDL 关键字。
- 表名白名单，强制注入 LIMIT，防止全表扫描 / 数据泄露。
- 复用受控的只读会话执行。
"""

from __future__ import annotations

import re
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models import User
from app.schemas import SqlQueryRequest, SqlQueryResult
from app.services import audit_service

router = APIRouter(prefix="/query", tags=["受控SQL查询"])

# 允许查询的表白名单
_ALLOWED_TABLES = {
    "stock_daily", "fund_nav", "instruments", "crawl_jobs", "crawl_runs",
    "export_records", "announcements", "data_quality_issues", "alert_records",
}
# 禁止的关键字（DML/DDL/危险函数）
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|replace|grant|"
    r"revoke|attach|detach|pragma|vacuum|reindex)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> str:
    """校验并规范化 SQL，返回安全的可执行语句，非法则抛 400。"""
    s = sql.strip().rstrip(";").strip()
    if not s:
        raise HTTPException(status_code=400, detail="SQL 不能为空")
    # 禁止多语句
    if ";" in s:
        raise HTTPException(status_code=400, detail="只允许执行单条 SQL 语句")
    # 必须是 SELECT 或 WITH
    if not re.match(r"^(select|with)\b", s, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="只允许 SELECT 查询语句")
    # 禁止 DML/DDL
    if _FORBIDDEN.search(s):
        raise HTTPException(status_code=400, detail="检测到非法关键字，仅允许只读查询")
    # 表名白名单校验：抓取 from / join 后的标识符
    referenced = set(re.findall(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", s, re.IGNORECASE))
    illegal = referenced - _ALLOWED_TABLES
    if illegal:
        raise HTTPException(
            status_code=400,
            detail=f"不允许访问的表：{', '.join(sorted(illegal))}；可查询：{', '.join(sorted(_ALLOWED_TABLES))}",
        )
    return s



def _strip_user_limit(sql: str) -> str:
    """移除尾部 LIMIT，由接口 limit 参数统一控制。复杂 LIMIT 写法直接拒绝。"""
    if re.search(r"\blimit\b", sql, re.IGNORECASE) is None:
        return sql
    stripped = re.sub(
        r"\s+limit\s+\d+\s*(?:offset\s+\d+)?\s*$",
        "",
        sql,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(
        r"\s+limit\s+\d+\s*,\s*\d+\s*$",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    if re.search(r"\blimit\b", stripped, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="LIMIT 请使用接口 limit 参数，不支持嵌套或复杂 LIMIT 写法")
    return stripped.strip()

@router.post("/sql", response_model=SqlQueryResult, summary="受控 SQL 查询（管理员，只读）")
def run_sql(
    payload: SqlQueryRequest,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> SqlQueryResult:
    safe_sql = _validate_sql(payload.sql)
    max_rows = min(payload.limit, settings.SQL_QUERY_MAX_ROWS)
    bounded_sql = _strip_user_limit(safe_sql)
    # 统一在外层强制 LIMIT，用户 SQL 的尾部 LIMIT 会被接口参数替代。
    exec_sql = f"SELECT * FROM ({bounded_sql}) AS _q LIMIT {max_rows + 1}"

    start = time.perf_counter()
    try:
        result = db.execute(text(exec_sql))
        columns = list(result.keys())
        fetched = result.fetchmany(max_rows + 1)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"SQL 执行错误：{exc}")
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    truncated = len(fetched) > max_rows
    rows = [dict(zip(columns, r)) for r in fetched[:max_rows]]

    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="sql_query",
        target="query/sql", detail=f"rows={len(rows)};sql={safe_sql[:120]}",
    )
    return SqlQueryResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
        elapsed_ms=elapsed_ms,
    )

