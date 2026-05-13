"""Touch Fish Guard 主入口"""
import sys
from src.main_controller import MainController
from src.utils.logger import logger


def main():
    """主函数"""
    try:
        # 创建主控制器
        controller = MainController("config.json")

        # 启动应用
        success = controller.start()

        if not success:
            logger.error("应用启动失败")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("收到中断信号")
        sys.exit(0)
    except Exception as e:
        logger.error(f"应用运行出错: {e}")
        logger.exception("详细错误信息:")
        sys.exit(1)


if __name__ == "__main__":
    main()
