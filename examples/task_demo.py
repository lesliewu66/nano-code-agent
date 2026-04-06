#!/usr/bin/env python3
"""
task_demo.py - Task System 独立演示
展示持久化任务管理的核心功能，不依赖 LLM。
"""
import json
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_system import TaskManager, TASKS_DIR


def demo():
    """演示 Task System 的核心功能"""
    # 使用临时目录避免污染主项目
    import tempfile
    import shutil
    
    tmp_dir = Path(tempfile.mkdtemp(prefix="task_demo_"))
    tasks = TaskManager(tmp_dir)
    
    print("=" * 60)
    print("Task System 演示")
    print("=" * 60)
    
    # 1. 创建任务
    print("\n1. 创建任务")
    print("-" * 40)
    
    t1 = json.loads(tasks.create("设计数据库", "设计用户表和订单表"))
    t2 = json.loads(tasks.create("实现 API", "RESTful 接口开发"))
    t3 = json.loads(tasks.create("前端页面", "React 组件开发"))
    t4 = json.loads(tasks.create("部署上线", "生产环境部署"))
    
    print(f"创建任务 #{t1['id']}: {t1['subject']}")
    print(f"创建任务 #{t2['id']}: {t2['subject']}")
    print(f"创建任务 #{t3['id']}: {t3['subject']}")
    print(f"创建任务 #{t4['id']}: {t4['subject']}")
    
    # 2. 设置依赖关系
    print("\n2. 设置依赖关系")
    print("-" * 40)
    print("API 依赖数据库设计")
    print("前端依赖 API")
    print("部署依赖前端")
    
    tasks.update(2, addBlockedBy=[1])  # API 依赖数据库
    tasks.update(3, addBlockedBy=[2])  # 前端依赖 API
    tasks.update(4, addBlockedBy=[3])  # 部署依赖前端
    
    print("\n当前任务列表:")
    print(tasks.list_all())
    
    # 3. 开始工作
    print("\n3. 开始处理任务 #1")
    print("-" * 40)
    tasks.update(1, status="in_progress")
    print(tasks.list_all())
    
    # 4. 完成任务，观察依赖自动解除
    print("\n4. 完成任务 #1 (观察依赖自动解除)")
    print("-" * 40)
    tasks.update(1, status="completed")
    print(tasks.list_all())
    
    print("\n注意：任务 #1 完成后，自动从 #2 的 blockedBy 中移除")
    
    # 5. 继续完成其他任务
    print("\n5. 继续完成任务 #2 和 #3")
    print("-" * 40)
    tasks.update(2, status="completed")
    tasks.update(3, status="completed")
    print(tasks.list_all())
    
    # 6. 查看存储的文件
    print("\n6. 查看持久化存储")
    print("-" * 40)
    print(f"任务存储目录: {tmp_dir}")
    print("文件列表:")
    for f in sorted(tmp_dir.glob("*.json")):
        task = json.loads(f.read_text())
        print(f"  {f.name}: {task['subject']} [{task['status']}]")
    
    # 7. 验证持久化
    print("\n7. 验证持久化 (创建新的 TaskManager 实例)")
    print("-" * 40)
    tasks2 = TaskManager(tmp_dir)
    print("新实例读取的任务列表:")
    print(tasks2.list_all())
    
    # 清理
    shutil.rmtree(tmp_dir)
    print(f"\n清理临时目录: {tmp_dir}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    demo()
