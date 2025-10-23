import os
import sys
from app import create_app, db
from models import ItemCategory, Item, Request, User, SystemConfig, Log, Notification
from werkzeug.security import generate_password_hash

def init_database():
    """初始化数据库"""
    app = create_app()
    with app.app_context():
        try:
            # 删除所有表
            print("删除现有表...")
            db.drop_all()
            
            # 创建所有表
            print("创建数据库表...")
            db.create_all()
            
            # 创建默认分类
            print("创建默认分类...")
            default_categories = [
                {"name": "办公用品", "description": "办公所需的各种物品"},
                {"name": "电子设备", "description": "电脑、手机等电子设备"},
                {"name": "实验器材", "description": "实验用的各种器材"},
                {"name": "工具设备", "description": "维修、建设等工具"},
                {"name": "书籍资料", "description": "各种书籍和资料"},
                {"name": "未分类", "description": "未分类的物品"}
            ]
            
            for cat_data in default_categories:
                category = ItemCategory(**cat_data)
                db.session.add(category)
            
            # 创建示例物品
            print("创建示例物品...")
            sample_items = [
                {"name": "A4打印纸", "category": "办公用品", "total": 1000, "in_stock": 850, "description": "标准A4打印纸，500张/包"},
                {"name": "中性笔", "category": "办公用品", "total": 200, "in_stock": 150, "description": "黑色中性笔"},
                {"name": "订书机", "category": "办公用品", "total": 20, "in_stock": 15, "description": "标准型订书机"},
                {"name": "笔记本电脑", "category": "电子设备", "total": 10, "in_stock": 7, "description": "高性能笔记本电脑"},
                {"name": "显示器", "category": "电子设备", "total": 15, "in_stock": 10, "description": "24英寸显示器"},
                {"name": "USB数据线", "category": "电子设备", "total": 50, "in_stock": 40, "description": "USB Type-C数据线"},
                {"name": "显微镜", "category": "实验器材", "total": 5, "in_stock": 4, "description": "生物显微镜"},
                {"name": "烧杯套装", "category": "实验器材", "total": 10, "in_stock": 8, "description": "玻璃烧杯套装"},
                {"name": "螺丝刀套装", "category": "工具设备", "total": 15, "in_stock": 12, "description": "多功能螺丝刀套装"},
                {"name": "扳手", "category": "工具设备", "total": 20, "in_stock": 18, "description": "开口扳手"},
                {"name": "专业参考书", "category": "书籍资料", "total": 30, "in_stock": 25, "description": "各领域专业参考书籍"},
                {"name": "文件夹", "category": "办公用品", "total": 100, "in_stock": 80, "description": "A4文件夹"}
            ]
            
            for item_data in sample_items:
                item = Item(**item_data)
                db.session.add(item)
            
            # 创建默认用户
            print("创建默认用户...")
            # 注意：在实际生产环境中，请使用更安全的密码
            default_users = [
                {"username": "admin", "password": generate_password_hash("admin123"), "role": "admin", "department": "IT部门"},
                {"username": "user", "password": generate_password_hash("user123"), "role": "user", "department": "研发部"}
            ]
            
            for user_data in default_users:
                user = User(**user_data)
                db.session.add(user)
            
            # 创建系统配置
            print("创建系统配置...")
            default_configs = [
                {"key": "system_name", "value": "仓库管理系统", "description": "系统名称"},
                {"key": "version", "value": "1.0.0", "description": "系统版本"},
                {"key": "max_borrow_days", "value": "14", "description": "最长借用天数"},
                {"key": "auto_approve_threshold", "value": "1", "description": "自动审批阈值"},
                {"key": "notification_enabled", "value": "true", "description": "是否启用通知"},
                {"key": "maintenance_mode", "value": "false", "description": "维护模式"}
            ]
            
            for config_data in default_configs:
                config = SystemConfig(**config_data)
                db.session.add(config)
            
            # 创建一条系统日志
            print("创建系统日志...")
            system_log = Log(
                username="system",
                action="系统初始化",
                details="数据库初始化完成",
                ip_address="127.0.0.1"
            )
            db.session.add(system_log)
            
            # 创建欢迎通知
            print("创建欢迎通知...")
            for username in ["admin", "user"]:
                notification = Notification(
                    username=username,
                    title="欢迎使用仓库管理系统",
                    content="系统已成功初始化，您可以开始使用了。",
                    type="system"
                )
                db.session.add(notification)
            
            # 提交所有更改
            db.session.commit()
            print("数据库初始化成功！")
            print("\n默认账户信息：")
            print("管理员: 用户名 admin, 密码 admin123")
            print("普通用户: 用户名 user, 密码 user123")
            print("\n请在首次登录后修改密码！")
            
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    init_database()