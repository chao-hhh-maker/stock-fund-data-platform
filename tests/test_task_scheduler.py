"""
第六步任务管理测试脚本
测试定时任务和手动触发功能
"""
import sys
sys.path.insert(0, 'backend')

from app.core.database import SessionLocal
from app.models.crawl import CrawlJob, CrawlRun
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_create_scheduled_task():
    """测试创建定时任务"""
    print("\n" + "=" * 60)
    print("测试 1: 创建定时任务")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 创建一个每天9点执行的股票采集任务
        job = CrawlJob(
            job_name="每日股票采集",
            job_type="stock_daily",
            schedule_cron="0 9 * * *",  # 每天9点
            is_enabled=1,
            extra_config='{"start_date": "20240101", "end_date": "20241231"}'
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"创建定时任务成功: job_id={job.id}")
        print(f"\n✅ 定时任务创建成功！")
        print(f"   任务ID: {job.id}")
        print(f"   任务名称: {job.job_name}")
        print(f"   CRON表达式: {job.schedule_cron}")
        print(f"   状态: {'启用' if job.is_enabled else '停用'}")
        
        return job.id
        
    except Exception as e:
        logger.error(f"创建定时任务失败: {e}")
        print(f"\n❌ 创建定时任务失败: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        db.close()


def test_enable_disable_task(job_id):
    """测试启用/停用任务"""
    print("\n" + "=" * 60)
    print("测试 2: 启用/停用任务")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        
        if not job:
            print("❌ 任务不存在")
            return False
        
        # 测试停用
        print(f"\n2.1 停用任务...")
        job.is_enabled = 0
        db.commit()
        logger.info(f"任务已停用: job_id={job_id}")
        print(f"   ✅ 任务已停用")
        
        # 验证
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        print(f"   当前状态: {'启用' if job.is_enabled else '停用'}")
        
        # 测试启用
        print(f"\n2.2 启用任务...")
        job.is_enabled = 1
        db.commit()
        logger.info(f"任务已启用: job_id={job_id}")
        print(f"   ✅ 任务已启用")
        
        # 验证
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        print(f"   当前状态: {'启用' if job.is_enabled else '停用'}")
        
        return True
        
    except Exception as e:
        logger.error(f"启用/停用任务失败: {e}")
        print(f"\n❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def test_manual_trigger():
    """测试手动触发任务"""
    print("\n" + "=" * 60)
    print("测试 3: 手动触发采集任务")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        from app.services.crawl_service import CrawlService
        
        # 创建任务记录
        job = CrawlJob(
            job_name="手动测试任务",
            job_type="stock_daily",
            is_enabled=1
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"创建测试任务: job_id={job.id}")
        
        # 执行采集
        service = CrawlService(db)
        records_count = service.crawl_stock_daily(
            job_id=job.id,
            stock_codes=['000001'],  # 平安银行
            start_date='20241201',
            end_date='20241231'
        )
        
        logger.info(f"手动采集完成: records={records_count}")
        print(f"\n✅ 手动触发成功！采集了 {records_count} 条记录")
        
        return True
        
    except Exception as e:
        logger.error(f"手动触发失败: {e}")
        print(f"\n❌ 手动触发失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def test_view_execution_history():
    """测试查看执行历史"""
    print("\n" + "=" * 60)
    print("测试 4: 查看任务执行历史")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 查询最近的执行记录
        runs = db.query(CrawlRun).order_by(
            CrawlRun.start_time.desc()
        ).limit(5).all()
        
        if not runs:
            print("\n⚠️  暂无执行记录")
            return True
        
        print(f"\n最近 {len(runs)} 条执行记录:")
        for i, run in enumerate(runs, 1):
            job = db.query(CrawlJob).filter(CrawlJob.id == run.job_id).first()
            job_name = job.job_name if job else "未知任务"
            
            print(f"\n{i}. 任务: {job_name}")
            print(f"   执行ID: {run.id}")
            print(f"   开始时间: {run.start_time}")
            print(f"   结束时间: {run.end_time or '未完成'}")
            print(f"   状态: {run.status}")
            print(f"   记录数: {run.records_count}")
            if run.error_message:
                print(f"   错误信息: {run.error_message[:100]}")
        
        print("\n✅ 执行历史查询成功")
        return True
        
    except Exception as e:
        logger.error(f"查询执行历史失败: {e}")
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def test_scheduler_lifecycle():
    """测试调度器生命周期"""
    print("\n" + "=" * 60)
    print("测试 5: 调度器生命周期")
    print("=" * 60)
    
    try:
        from app.tasks.scheduler.scheduler_manager import scheduler_manager
        
        # 测试启动
        print("\n5.1 启动调度器...")
        scheduler_manager.start()
        print(f"   ✅ 调度器状态: {'运行中' if scheduler_manager.scheduler.running else '未运行'}")
        
        # 加载任务
        print("\n5.2 从数据库加载任务...")
        scheduler_manager.load_jobs_from_database()
        print(f"   ✅ 任务加载完成")
        
        # 测试关闭
        print("\n5.3 关闭调度器...")
        scheduler_manager.shutdown(wait=False)
        print(f"   ✅ 调度器状态: {'运行中' if scheduler_manager.scheduler.running else '已关闭'}")
        
        return True
        
    except Exception as e:
        logger.error(f"调度器生命周期测试失败: {e}")
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "🚀" * 30)
    print("  第六步任务管理功能测试")
    print("🚀" * 30)
    
    results = []
    
    # 测试1: 创建定时任务
    job_id = test_create_scheduled_task()
    results.append(("创建定时任务", job_id is not None))
    
    # 测试2: 启用/停用任务
    if job_id:
        results.append(("启用/停用任务", test_enable_disable_task(job_id)))
    
    # 测试3: 手动触发
    results.append(("手动触发任务", test_manual_trigger()))
    
    # 测试4: 查看执行历史
    results.append(("查看执行历史", test_view_execution_history()))
    
    # 测试5: 调度器生命周期
    results.append(("调度器生命周期", test_scheduler_lifecycle()))
    
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
        print("\n🎉 所有测试通过！第六步已完成！")
        print("\n可以访问 Swagger 文档测试 API:")
        print("  http://localhost:8001/docs")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())
