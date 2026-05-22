"""
数据库验证脚本
用于检查数据库表结构是否正确创建
"""
import sys
import io
from pathlib import Path

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


def verify_database():
    """验证数据库表结构"""
    try:
        from sqlalchemy import create_engine, inspect, text
        from dotenv import load_dotenv
        import os

        # 加载环境变量
        env_file = backend_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ 错误: 未找到DATABASE_URL环境变量")
            return False

        print(f"连接到数据库: {database_url}")
        engine = create_engine(database_url)

        # 检查连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()
            print(f"✅ 数据库连接成功 - MySQL版本: {version[0]}")

        # 获取所有表
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 期望的表列表
        expected_tables = [
            "users",
            "roles",
            "instruments",
            "stock_daily",
            "fund_nav",
            "crawl_jobs",
            "crawl_runs",
            "export_records",
        ]

        print(f"\n数据库中的表 ({len(tables)}个):")
        for table in tables:
            status = "✅" if table in expected_tables else "⚠️"
            print(f"  {status} {table}")

        # 检查是否所有必需的表都存在
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f"\n❌ 缺少的表: {', '.join(missing_tables)}")
            return False
        else:
            print(f"\n✅ 所有{len(expected_tables)}个核心表都已创建")

        # 检查每个表的结构
        print("\n表结构详情:")
        for table in expected_tables:
            columns = inspector.get_columns(table)
            print(f"\n📋 {table} 表 ({len(columns)}个字段):")
            for col in columns:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                print(f"   - {col['name']}: {col['type']} {nullable}")

            # 检查索引
            indexes = inspector.get_indexes(table)
            if indexes:
                print(f"   索引 ({len(indexes)}个):")
                for idx in indexes:
                    unique = "UNIQUE" if idx["unique"] else "INDEX"
                    print(f"     {unique}: {idx['name']} ({', '.join(idx['column_names'])})")

        # 检查外键
        print("\n\n外键关系:")
        for table in expected_tables:
            fks = inspector.get_foreign_keys(table)
            if fks:
                for fk in fks:
                    print(f"  {table}.{fk['constrained_columns'][0]} -> {fk['referred_table']}.{fk['referred_columns'][0]}")

        # 检查初始数据
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM roles"))
            role_count = result.fetchone()[0]
            print(f"\n✅ 角色表初始数据: {role_count}条")

            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"✅ 用户表初始数据: {user_count}条")

        print("\n" + "="*60)
        print("✅ 数据库验证通过! 所有核心表结构正确")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n❌ 数据库验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
