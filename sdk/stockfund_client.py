"""股票基金数据平台 Python SDK（模块4：Python 封装）。

对平台 RESTful API 的轻量封装，便于在脚本 / 量化研究中复用：

    from stockfund_client import StockFundClient

    cli = StockFundClient("http://127.0.0.1:8000")
    cli.login("admin", "admin123")
    df = cli.stock_daily("600519.SH")          # 返回 pandas.DataFrame（若装了 pandas）
    nav = cli.fund_nav("510300.OF")
    cli.crawl(job_type="stock_daily", target_codes="600519.SH")
    rows = cli.sql("SELECT code, COUNT(*) c FROM stock_daily GROUP BY code")

依赖：requests（必需），pandas（可选，用于 DataFrame 输出）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests


class StockFundClient:
    """平台 API 客户端。"""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 30) -> None:
        self.base = base_url.rstrip("/")
        self.api = f"{self.base}/api"
        self.timeout = timeout
        self._token: Optional[str] = None
        self._session = requests.Session()

    # ---------- 认证 ----------
    def login(self, username: str, password: str) -> Dict[str, Any]:
        resp = self._session.post(
            f"{self.api}/auth/login",
            json={"username": username, "password": password},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._session.headers["Authorization"] = f"Bearer {self._token}"
        return data

    def _get(self, path: str, params: Optional[Dict] = None) -> Any:
        resp = self._session.get(f"{self.api}{path}", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: Optional[Dict] = None) -> Any:
        resp = self._session.post(f"{self.api}{path}", json=body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ---------- 查询 ----------
    def instruments(self, asset_type: Optional[str] = None, page_size: int = 200) -> List[Dict]:
        params = {"page_size": page_size}
        if asset_type:
            params["asset_type"] = asset_type
        return self._get("/instruments", params)["items"]

    def stock_daily(self, code: str, start_date: Optional[str] = None,
                    end_date: Optional[str] = None, page_size: int = 500):
        params = {"page_size": page_size}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        items = self._get(f"/stocks/{code}/daily", params)["items"]
        return self._to_frame(items)

    def fund_nav(self, code: str, start_date: Optional[str] = None,
                 end_date: Optional[str] = None, page_size: int = 500):
        params = {"page_size": page_size}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        items = self._get(f"/funds/{code}/nav", params)["items"]
        return self._to_frame(items)

    # ---------- 采集 / 导出 / SQL ----------
    def crawl(self, job_type: str, target_codes: str, mode: str = "full") -> Dict:
        return self._post("/tasks/crawl", {
            "job_type": job_type, "target_codes": target_codes, "mode": mode,
        })

    def export(self, dataset: str, file_format: str = "csv", code: Optional[str] = None,
               compress: bool = False, encrypt: bool = False) -> Dict:
        return self._post("/exports", {
            "dataset": dataset, "file_format": file_format, "code": code,
            "compress": compress, "encrypt": encrypt,
        })

    def sql(self, sql: str, limit: int = 200) -> List[Dict]:
        """执行受控只读 SQL 查询（需管理员账号）。"""
        return self._post("/query/sql", {"sql": sql, "limit": limit})["rows"]

    def dashboard(self) -> Dict:
        return self._get("/dashboard")

    @staticmethod
    def _to_frame(items: List[Dict]):
        """有 pandas 则返回 DataFrame，否则原样返回列表。"""
        try:
            import pandas as pd

            return pd.DataFrame(items)
        except ImportError:
            return items


if __name__ == "__main__":
    # 简易自测：登录并拉取一只股票日线
    cli = StockFundClient("http://127.0.0.1:8000")
    print("登录:", cli.login("admin", "admin123")["username"])
    print("标的数:", len(cli.instruments()))
    df = cli.stock_daily("600519.SH", page_size=5)
    print("行情样例:\n", df)
    print("SQL:", cli.sql("SELECT COUNT(*) AS n FROM stock_daily"))
