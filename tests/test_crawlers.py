"""
第五步采集器测试脚本
测试股票和基金数据采集功能
"""
import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.services.crawl_service import CrawlService
from app.models.crawl import CrawlJob
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_stock_crawler():
    """测试股票日线采集器"""
    print("\n" + "=" * 60)
    print("测试 1: 股票日线采集器")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建任务记录
        job = CrawlJob(
            job_name="测试股票采集",
            job_type="stock_daily",
            is_enabled=1
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"创建测试任务: job_id={job.id}")
        
        # 执行采集（使用测试股票代码）
        service = CrawlService(db)
        records_count = service.crawl_stock_daily(
            job_id=job.id,
            stock_codes=['000001'],  # 平安银行
            start_date='20240101',
            end_date='20241231'
        )
        
        logger.info(f"股票采集完成，共 {records_count} 条记录")
        print(f"\n✅ 股票采集成功！采集了 {records_count} 条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"股票采集测试失败: {e}")
        print(f"\n❌ 股票采集测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def test_fund_crawler():
    """测试基金净值采集器"""
    print("\n" + "=" * 60)
    print("测试 2: 基金净值采集器")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建任务记录
        job = CrawlJob(
            job_name="测试基金采集",
            job_type="fund_nav",
            is_enabled=1
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"创建测试任务: job_id={job.id}")
        
        # 执行采集（使用测试基金代码）
        service = CrawlService(db)
        records_count = service.crawl_fund_nav(
            job_id=job.id,
            fund_codes=['000001'],  # 华夏成长混合
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        logger.info(f"基金采集完成，共 {records_count} 条记录")
        print(f"\n✅ 基金采集成功！采集了 {records_count} 条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"基金采集测试失败: {e}")
        print(f"\n❌ 基金采集测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def verify_database():
    """验证数据库中的数据"""
    print("\n" + "=" * 60)
    print("测试 3: 验证数据库数据")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        from app.models.stock_daily import StockDaily
        from app.models.fund_nav import FundNav
        from app.models.crawl import CrawlRun
        
        # 检查股票数据
        stock_count = db.query(StockDaily).count()
        print(f"\n股票日线数据: {stock_count} 条")
        
        if stock_count > 0:
            sample = db.query(StockDaily).first()
            print(f"  示例: code={sample.code}, date={sample.trade_date}, close={sample.close}")
        
        # 检查基金数据
        fund_count = db.query(FundNav).count()
        print(f"基金净值数据: {fund_count} 条")
        
        if fund_count > 0:
            sample = db.query(FundNav).first()
            print(f"  示例: code={sample.code}, date={sample.nav_date}, nav={sample.unit_nav}")
        
        # 检查采集记录
        run_count = db.query(CrawlRun).count()
        print(f"采集执行记录: {run_count} 条")
        
        if run_count > 0:
            runs = db.query(CrawlRun).order_by(CrawlRun.id.desc()).limit(3).all()
            for run in runs:
                print(f"  - run_id={run.id}, status={run.status}, records={run.records_count}")
        
        print("\n✅ 数据库验证完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库验证失败: {e}")
        print(f"\n❌ 数据库验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def main():
    print("\n" + "🚀" * 30)
    print("  第五步采集器功能测试")
    print("🚀" * 30)
    
    results = []
    
    # 测试股票采集
    results.append(("股票采集器", test_stock_crawler()))
    
    # 测试基金采集
    results.append(("基金采集器", test_fund_crawler()))
    
    # 验证数据库
    results.append(("数据库验证", verify_database()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")
    
    print("\n" + "-" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！第五步已完成！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
