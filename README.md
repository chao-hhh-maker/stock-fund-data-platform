# stock-fund-data-platform
## 📌 项目简介
本项目是一个全链路的金融数据平台，覆盖"股票与基金数据的采集、清洗、存储、查询与运维"全流程，支持多数据源接入、数据标准化处理、高性能查询接口及完善的权限管理，为量化分析、投研决策提供可靠的数据支撑。

## 🛠️ 技术栈
- 开发语言：Python 3.10+
- 数据采集：akshare、tushare、requests、APScheduler
- 数据处理：pandas、numpy
- 数据存储：Redis、ClickHouse、MongoDB
- API服务：FastAPI、WebSocket
- 监控运维：Prometheus、Grafana、loguru
- 权限管理：RBAC模型


## 📂 项目结构
```text
stock-fund-data-platform/
├── README.md              # 项目说明文档
├── requirements.txt       # 依赖包列表
├── .gitignore             # Git忽略文件配置
├── config/                # 全局配置目录
│   ├── settings.py        # 系统配置（数据库连接、API密钥等）
│   ├── scheduler.yaml     # 采集任务调度配置
│   └── permissions.yaml   # 权限控制配置
├── src/                   # 核心代码目录
│   ├── crawler/           # 1. 数据获取与采集模块
│   │   ├── providers/     # 多数据源接入
│   │   │   ├── wind_api.py
│   │   │   ├── eastmoney_api.py
│   │   │   ├── akshare_api.py
│   │   │   └── tushare_api.py
│   │   ├── scheduler.py    # 采集任务调度（定时/增量/全量）
│   │   ├── monitor.py      # 采集任务监控与告警
│   │   └── retry_handler.py # 智能重试机制
│   ├── cleaner/           # 2. 数据清洗与标准化模块
│   │   ├── missing_handler.py   # 缺失值处理
│   │   ├── anomaly_handler.py   # 异常值处理
│   │   ├── validator.py         # 数据一致性校验
│   │   └── standardizer.py      # 数据标准化（代码/行业/净值）
│   ├── storage/           # 3. 数据存储与管理模块
│   │   ├── redis_store.py       # 实时数据缓存
│   │   ├── clickhouse_store.py  # 历史数据列式存储
│   │   ├── mongo_store.py       # 文档型数据存储
│   │   └── metadata.py          # 元数据管理（数据字典/血缘）
│   ├── api/               # 4. 数据查询与API服务模块
│   │   ├── sql_interface.py     # 通用SQL查询接口
│   │   ├── rest_api.py          # RESTful API服务
│   │   ├── websocket.py         # WebSocket实时推送
│   │   ├── exporter.py          # 多格式数据导出
│   │   └── query_optimizer.py   # 查询性能优化
│   ├── monitor_ops/       # 5. 数据监控与运维模块
│   │   ├── data_monitor.py      # 数据完整性监控
│   │   ├── system_monitor.py    # 系统健康监控
│   │   └── alert.py             # 告警通知
│   └── auth/              # 6. 用户权限与安全管理模块
│       ├── rbac.py              # 基于角色的权限控制
│       ├── quota.py             # 用量配额管理
│       └── audit.py             # 操作审计日志
├── tests/                 # 单元测试目录
│   ├── test_crawler.py
│   ├── test_cleaner.py
│   ├── test_storage.py
│   ├── test_api.py
│   ├── test_monitor.py
│   └── test_auth.py
├── docs/                  # 项目文档目录
│   ├── api.md               # API接口文档
│   ├── deployment.md        # 部署指南
│   └── design.md            # 系统设计说明
└── logs/                  # 日志目录（.gitignore中忽略）


## ✨ 核心功能模块

### 1. 数据获取与采集模块
- 多渠道数据源接入：集成 Wind、同花顺、东方财富、新浪等主流金融数据供应商 API；整合 akshare、Tushare 等第三方开源数据；支持证监会公告、上市公司年报、金融新闻与舆情等公开数据源抓取；对接宏观经济、行业数据、另类数据等第三方数据服务。
- 灵活采集调度：支持实时、分钟级、日级、季度级等多维度更新频率配置；内置智能重试机制与失败告警通知；提供增量采集与全量更新双策略；实现采集任务监控与资源调度管理。

### 2. 数据清洗与标准化模块
- 数据质量控制：自动识别并处理缺失值、异常值；开展数据一致性校验（如复权价格逻辑验证）；建立跨数据源交叉验证机制；支持人工数据检查与校对流程。
- 标准化处理能力：实现统一证券代码映射（新旧代码转换）；完成财务数据标准化（适配不同会计准则）；支持基金净值复权计算（分红、拆分场景）；提供申万、中信、GICS 等多套行业分类体系统一映射。

### 3. 数据存储与管理模块
- 多层次存储架构：采用 Redis/内存数据库实现实时数据缓存；使用 ClickHouse 存储海量历史数据；通过 MongoDB/Elasticsearch 存储公告、舆情等文档型数据。
- 元数据全生命周期管理：维护完整数据字典与字段说明；支持数据血缘关系追踪；标注数据更新频率与时效性；实现数据权限与敏感级别分级标记。

### 4. 数据查询与API服务模块
- 多样化查询接口：提供通用 SQL 查询接口、RESTful API 服务、WebSocket 实时数据推送；支持 Python 封装调用，方便二次开发。
- 查询性能优化：高频查询结果缓存、分页查询与流式返回、复杂查询性能优化；配置查询权限控制与接口限流策略。
- 数据导出功能：支持 CSV、Excel、Parquet 等多格式数据导出；实现批量导出任务管理；提供导出数据加密与压缩；记录完整导出历史操作日志。

### 5. 数据监控与运维模块
- 数据完整性监控：每日数据更新完整性检查；关键字段数据异常监测；数据延迟与滞后告警；节假日及特殊日期任务自动适配处理。
- 系统健康监控：数据采集任务运行状态监控；服务器存储空间与资源使用监控；API 服务性能与可用性监控告警。

### 6. 用户权限与安全管理模块
- 多租户数据隔离：支持机构级、部门级、个人用户多级数据隔离与访问控制。
- 精细化权限管理：实现功能权限（查询、导出、管理等）、数据权限（字段级、行级控制）、时间权限（历史数据访问时限）三维管控；配置接口调用与数据导出用量配额管理，保障数据安全合规。
