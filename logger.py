import logging
import os
from datetime import datetime

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


class PrefixFormatter(logging.Formatter):
    """自定义格式化器，为 DEBUG 级别日志添加开源项目前缀"""

    def format(self, record):
        if record.levelno == logging.DEBUG:  # 只给 DEBUG 级别添加前缀
            record.msg = f"[开源项目：https://github.com/chengazhen/cursor-auto-free] {record.msg}"
        return super().format(record)


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log"),
            encoding="utf-8",
        ),
    ],
)

# 为文件处理器设置自定义格式化器
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setFormatter(
            PrefixFormatter("%(asctime)s - %(levelname)s - %(message)s")
        )


# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(PrefixFormatter("%(message)s"))

# 将控制台处理器添加到日志记录器
logging.getLogger().addHandler(console_handler)

# 打印日志目录所在路径
logging.info(f"Logger initialized, log directory: {os.path.abspath(log_dir)}")


def main_task():
    """
    Main task execution function. Simulates a workflow and handles errors.
    """
    try:
        logging.info("Starting the main task...")

        # Simulated task and error condition
        if some_condition():
            raise ValueError("Simulated error occurred.")

        logging.info("Main task completed successfully.")

    except ValueError as ve:
        logging.error(f"ValueError occurred: {ve}", exc_info=True)
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}", exc_info=True)
    finally:
        logging.info("Task execution finished.")


def some_condition():
    """
    Simulates an error condition. Returns True to trigger an error.
    Replace this logic with actual task conditions.
    """
    return True


if __name__ == "__main__":
    # Application workflow
    logging.info("Application started.")
    main_task()
    logging.info("Application exited.")
