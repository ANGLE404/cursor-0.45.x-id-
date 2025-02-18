import os
import platform
import json
import sys
from colorama import Fore, Style, init
from enum import Enum
from typing import Optional
import threading
import time

# 注释掉机器码相关的导入
# from exit_cursor import ExitCursor
# import go_cursor_help
# import patch_cursor_get_machine_id
# from reset_machine import MachineIDResetter

os.environ["PYTHONVERBOSE"] = "0"
os.environ["PYINSTALLER_VERBOSE"] = "0"

import random
from cursor_auth_manager import CursorAuthManager
import os
from logger import logging
from browser_utils import BrowserManager
from get_email_code import EmailVerificationHandler
from logo import print_logo
from config import Config
from datetime import datetime

# 初始化colorama
init()

# 定义颜色主题
class Colors:
    # 基础颜色
    PRIMARY = Fore.CYAN
    SUCCESS = Fore.GREEN
    ERROR = Fore.RED
    WARNING = Fore.YELLOW
    INFO = Fore.BLUE
    TITLE = Fore.MAGENTA
    
    # 扩展颜色
    PURPLE = Fore.MAGENTA
    WHITE = Fore.WHITE
    GREY = "\033[90m"
    ORANGE = "\033[38;5;208m"
    PINK = "\033[38;5;206m"
    LIME = "\033[38;5;119m"
    TEAL = "\033[38;5;31m"
    
    # 样式
    RESET = Style.RESET_ALL
    BRIGHT = Style.BRIGHT
    DIM = Style.DIM

# 定义 Emoji 字典
EMOJI = {
    "ERROR": "❌",
    "WARNING": "⚠️",
    "INFO": "ℹ️",
    "SUCCESS": "✅",
    "START": "🚀",
    "END": "🎉",
    "KEY": "🔑",
    "MAIL": "📧",
    "BROWSER": "🌐",
    "STAR": "⭐",
    "GEAR": "⚙️",
    "LOCK": "🔒",
    "UNLOCK": "🔓",
    "TIME": "⏰",
    "CHECK": "✔️",
    "LOADING": "⏳",
    "SPARK": "✨",
    "FIRE": "🔥"
}

# 定义加载动画字符
SPINNER_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

class Spinner:
    def __init__(self, message=""):
        self.message = message
        self.running = False
        self.spinner_thread = None

    def spin(self):
        while self.running:
            for char in SPINNER_CHARS:
                if not self.running:
                    break
                print(f"\r{Colors.INFO}{char} {self.message}{Colors.RESET}", end="")
                time.sleep(0.1)

    def start(self):
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.start()

    def stop(self):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()
        print("\r" + " " * (len(self.message) + 2), end="\r")

def print_box(message: str, style: str = Colors.PRIMARY, emoji: str = "") -> None:
    """打印带框的消息"""
    width = len(message) + 4
    if emoji:
        message = f"{emoji}  {message}"
        width += 4
    print(f"{style}╭{'─' * width}╮")
    print(f"│  {message}  │")
    print(f"╰{'─' * width}╯{Colors.RESET}")

def print_step(message: str, emoji: str = EMOJI["STAR"]) -> None:
    """打印步骤信息"""
    print(f"\n{Colors.BRIGHT}{Colors.TEAL}{emoji} {message}{Colors.RESET}")

# 修改原有的 logging 输出
class ColoredLogger:
    @staticmethod
    def info(message: str) -> None:
        print(f"{Colors.INFO}{EMOJI['INFO']} {message}{Colors.RESET}")

    @staticmethod
    def error(message: str) -> None:
        print(f"{Colors.ERROR}{EMOJI['ERROR']} {message}{Colors.RESET}")

    @staticmethod
    def warning(message: str) -> None:
        print(f"{Colors.WARNING}{EMOJI['WARNING']} {message}{Colors.RESET}")

    @staticmethod
    def success(message: str) -> None:
        print(f"{Colors.SUCCESS}{EMOJI['SUCCESS']} {message}{Colors.RESET}")

    @staticmethod
    def debug(message: str) -> None:
        print(f"{Colors.PURPLE}{EMOJI['GEAR']} {message}{Colors.RESET}")
logging = ColoredLogger()

def print_menu():
    """打印美化的菜单"""
    print_box("Cursor Pro Keep Alive", Colors.BRIGHT + Colors.PINK, EMOJI["FIRE"])
    print(f"\n{Colors.TEAL}{EMOJI['START']} 自动注册程序已启动{Colors.RESET}")
    print(f"{Colors.PRIMARY}{'─' * 30}{Colors.RESET}")

def print_end_message():
    print_box("操作完成", Colors.SUCCESS, EMOJI["END"])
    print(f"\n{Colors.BRIGHT}{Colors.LIME}=== 获取更多信息 ==={Colors.RESET}")
    print(f"{Colors.PRIMARY}{'─' * 30}{Colors.RESET}")
    print(f"{Colors.BRIGHT}{Colors.ORANGE}https://github.com/chengazhen/cursor-auto-free{Colors.RESET}\n")

class VerificationStatus(Enum):
    """验证状态枚举"""

    PASSWORD_PAGE = "@name=password"
    CAPTCHA_PAGE = "@data-index=0"
    ACCOUNT_SETTINGS = "Account Settings"


class TurnstileError(Exception):
    """Turnstile 验证相关异常"""

    pass


def check_verification_success(tab) -> Optional[VerificationStatus]:
    """
    检查验证是否成功

    Returns:
        VerificationStatus: 验证成功时返回对应状态，失败返回 None
    """
    for status in VerificationStatus:
        if tab.ele(status.value):
            logging.info(f"验证成功 - 已到达{status.name}页面")
            return status
    return None


def handle_turnstile(tab, max_retries: int = 2, retry_interval: tuple = (1, 2)) -> bool:
    """处理 Turnstile 验证"""
    logging.info(f"{EMOJI['LOCK']} 正在检测 Turnstile 验证...")

    retry_count = 0
    try:
        while retry_count < max_retries:
            retry_count += 1
            logging.debug(f"第 {retry_count} 次尝试验证")

            try:
                challenge_check = (
                    tab.ele("@id=cf-turnstile", timeout=2)
                    .child()
                    .shadow_root.ele("tag:iframe")
                    .ele("tag:body")
                    .sr("tag:input")
                )

                if challenge_check:
                    logging.info(f"{EMOJI['GEAR']} 检测到 Turnstile 验证框，开始处理...")
                    time.sleep(random.uniform(1, 3))
                    challenge_check.click()
                    time.sleep(2)

                    if check_verification_success(tab):
                        logging.info(f"{EMOJI['UNLOCK']} Turnstile 验证通过")
                        return True

            except Exception as e:
                logging.debug(f"当前尝试未成功: {str(e)}")

            if check_verification_success(tab):
                return True

            time.sleep(random.uniform(*retry_interval))

        logging.error(f"验证失败 - 已达到最大重试次数 {max_retries}")
        return False

    except Exception as e:
        error_msg = f"Turnstile 验证过程发生异常: {str(e)}"
        logging.error(error_msg)
        raise TurnstileError(error_msg)


def get_cursor_session_token(tab, max_attempts=3, retry_interval=2):
    """
    获取Cursor会话token，带有重试机制
    :param tab: 浏览器标签页
    :param max_attempts: 最大尝试次数
    :param retry_interval: 重试间隔(秒)
    :return: session token 或 None
    """
    logging.info("开始获取cookie")
    attempts = 0

    while attempts < max_attempts:
        try:
            cookies = tab.cookies()
            for cookie in cookies:
                if cookie.get("name") == "WorkosCursorSessionToken":
                    return cookie["value"].split("%3A%3A")[1]

            attempts += 1
            if attempts < max_attempts:
                logging.warning(
                    f"第 {attempts} 次尝试未获取到CursorSessionToken，{retry_interval}秒后重试..."
                )
                time.sleep(retry_interval)
            else:
                logging.error(
                    f"已达到最大尝试次数({max_attempts})，获取CursorSessionToken失败"
                )

        except Exception as e:
            logging.error(f"获取cookie失败: {str(e)}")
            attempts += 1
            if attempts < max_attempts:
                logging.info(f"将在 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)

    return None


def update_cursor_auth(email=None, access_token=None, refresh_token=None):
    """
    更新Cursor的认证信息的便捷函数
    """
    auth_manager = CursorAuthManager()
    return auth_manager.update_auth(email, access_token, refresh_token)


def sign_up_account(browser, tab):
    logging.info("=== 开始注册账号流程 ===")
    logging.info(f"正在访问注册页面: {sign_up_url}")
    tab.get(sign_up_url)

    try:
        if tab.ele("@name=first_name"):
            logging.info("正在填写个人信息...")
            tab.actions.click("@name=first_name").input(first_name)
            logging.info(f"已输入名字: {first_name}")
            time.sleep(random.uniform(1, 3))

            tab.actions.click("@name=last_name").input(last_name)
            logging.info(f"已输入姓氏: {last_name}")
            time.sleep(random.uniform(1, 3))

            tab.actions.click("@name=email").input(account)
            logging.info(f"已输入邮箱: {account}")
            time.sleep(random.uniform(1, 3))

            logging.info("提交个人信息...")
            tab.actions.click("@type=submit")

    except Exception as e:
        logging.error(f"注册页面访问失败: {str(e)}")
        return False

    handle_turnstile(tab)

    try:
        if tab.ele("@name=password"):
            logging.info("正在设置密码...")
            tab.ele("@name=password").input(password)
            time.sleep(random.uniform(1, 3))

            logging.info("提交密码...")
            tab.ele("@type=submit").click()
            logging.info("密码设置完成，等待系统响应...")

    except Exception as e:
        logging.error(f"密码设置失败: {str(e)}")
        return False

    if tab.ele("This email is not available."):
        logging.error("注册失败：邮箱已被使用")
        return False

    handle_turnstile(tab)

    while True:
        try:
            if tab.ele("Account Settings"):
                logging.info("注册成功 - 已进入账户设置页面")
                break
            if tab.ele("@data-index=0"):
                logging.info("正在获取邮箱验证码...")
                code = email_handler.get_verification_code()
                if not code:
                    logging.error("获取验证码失败")
                    return False

                logging.info(f"成功获取验证码: {code}")
                logging.info("正在输入验证码...")
                i = 0
                for digit in code:
                    tab.ele(f"@data-index={i}").input(digit)
                    time.sleep(random.uniform(0.1, 0.3))
                    i += 1
                logging.info("验证码输入完成")
                break
        except Exception as e:
            logging.error(f"验证码处理过程出错: {str(e)}")

    handle_turnstile(tab)
    wait_time = random.randint(3, 6)
    for i in range(wait_time):
        logging.info(f"等待系统处理中... 剩余 {wait_time-i} 秒")
        time.sleep(1)

    logging.info("正在获取账户信息...")
    tab.get(settings_url)
    try:
        usage_selector = (
            "css:div.col-span-2 > div > div > div > div > "
            "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
            "span.font-mono.text-sm\\/\\[0\\.875rem\\]"
        )
        usage_ele = tab.ele(usage_selector)
        if usage_ele:
            usage_info = usage_ele.text
            total_usage = usage_info.split("/")[-1].strip()
            logging.info(f"账户可用额度上限: {total_usage}")
            logging.info(
                "加入用户交流QQ群获取支持：994997809\n遇到问题可随时在群内反馈，开发者实时答疑\n开源地址保留（自愿star）：https://github.com/ANGLE404/cursor-0.45.x-id-\n\n💡 小提示：加群可获取最新版本提醒和独家使用技巧哦~"
            )
    except Exception as e:
        logging.error(f"获取账户额度信息失败: {str(e)}")

    logging.info("\n=== 注册完成 ===")
    account_info = f"Cursor 账号信息:\n邮箱: {account}\n密码: {password}"
    logging.info(account_info)
    time.sleep(5)
    return True


class EmailGenerator:
    def __init__(
        self,
        password="".join(
            random.choices(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
                k=12,
            )
        ),
    ):
        configInstance = Config()
        configInstance.print_config()
        self.domain = configInstance.get_domain()
        self.default_password = password
        self.default_first_name = self.generate_random_name()
        self.default_last_name = self.generate_random_name()

    def generate_random_name(self, length=6):
        """生成随机用户名"""
        first_letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        rest_letters = "".join(
            random.choices("abcdefghijklmnopqrstuvwxyz", k=length - 1)
        )
        return first_letter + rest_letters

    def generate_email(self, length=8):
        """生成随机邮箱地址"""
        random_str = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=length))
        timestamp = str(int(time.time()))[-6:]  # 使用时间戳后6位
        return f"{random_str}{timestamp}@{self.domain}"

    def get_account_info(self):
        """获取完整的账号信息"""
        return {
            "email": self.generate_email(),
            "password": self.default_password,
            "first_name": self.default_first_name,
            "last_name": self.default_last_name,
        }


def get_user_agent():
    """获取user_agent"""
    try:
        # 使用JavaScript获取user agent
        browser_manager = BrowserManager()
        browser = browser_manager.init_browser()
        user_agent = browser.latest_tab.run_js("return navigator.userAgent")
        browser_manager.quit()
        return user_agent
    except Exception as e:
        logging.error(f"获取user agent失败: {str(e)}")
        return None


# 注释掉机器码检查函数
"""
def check_cursor_version():
    pkg_path, main_path = patch_cursor_get_machine_id.get_cursor_paths()
    with open(pkg_path, "r", encoding="utf-8") as f:
        version = json.load(f)["version"]
    return patch_cursor_get_machine_id.version_check(version, min_version="0.45.0")

def reset_machine_id(greater_than_0_45):
    if greater_than_0_45:
        go_cursor_help.go_cursor_help()
    else:
        MachineIDResetter().reset_machine_ids()
"""

if __name__ == "__main__":
    print_logo()
    # 注释掉机器码版本检查
    # greater_than_0_45 = check_cursor_version()
    browser_manager = None
    try:
        print_step(f"初始化程序", EMOJI["GEAR"])
        # 注释掉ExitCursor
        # ExitCursor()

        print_menu()
        
        # 移除选项菜单，直接进入注册流程
        choice = 2  # 直接设置为注册流程

        logging.info(f"{EMOJI['BROWSER']} 正在初始化浏览器...")

        # 获取user_agent
        user_agent = get_user_agent()
        if not user_agent:
            logging.error("获取user agent失败，使用默认值")
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # 剔除user_agent中的"HeadlessChrome"
        user_agent = user_agent.replace("HeadlessChrome", "Chrome")

        spinner = Spinner(f"{EMOJI['LOADING']} 正在初始化浏览器...")
        spinner.start()
        browser_manager = BrowserManager()
        browser = browser_manager.init_browser(user_agent)
        spinner.stop()
        logging.success(f"{EMOJI['CHECK']} 浏览器初始化完成")

        # 获取并打印浏览器的user-agent
        user_agent = browser.latest_tab.run_js("return navigator.userAgent")

        logging.info(f"{EMOJI['MAIL']} 正在初始化邮箱验证模块...")
        email_handler = EmailVerificationHandler()
        logging.info(
            "请前往开源项目查看更多信息：https://github.com/chengazhen/cursor-auto-free"
        )
        logging.info(f"\n{Colors.BRIGHT}{Colors.TEAL}=== 配置信息 ==={Colors.RESET}")
        login_url = "https://authenticator.cursor.sh"
        sign_up_url = "https://authenticator.cursor.sh/sign-up"
        settings_url = "https://www.cursor.com/settings"

        logging.info("正在生成随机账号信息...")
        email_generator = EmailGenerator()
        account = email_generator.generate_email()
        password = email_generator.default_password
        first_name = email_generator.default_first_name
        last_name = email_generator.default_last_name

        logging.info(f"生成的邮箱账号: {account}")
        auto_update_cursor_auth = True

        tab = browser.latest_tab

        tab.run_js("try { turnstile.reset() } catch(e) { }")

        logging.info("\n=== 开始注册流程 ===")
        logging.info(f"正在访问登录页面: {login_url}")
        tab.get(login_url)

        if sign_up_account(browser, tab):
            logging.info(f"{EMOJI['KEY']} 正在获取会话令牌...")
            token = get_cursor_session_token(tab)
            if token:
                logging.info(f"{EMOJI['SPARK']} 更新认证信息...")
                update_cursor_auth(email=account, access_token=token, refresh_token=token)
                logging.info(f"{EMOJI['STAR']} 所有操作已完成")
                print_end_message()
            else:
                logging.error("获取会话令牌失败，注册流程未完成")

    except Exception as e:
        logging.error(f"程序执行出现错误: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
    finally:
        if browser_manager:
            browser_manager.quit()
        input(f"\n{Colors.BRIGHT}{Colors.TEAL}{EMOJI['END']} 程序执行完毕，按回车键退出...{Colors.RESET}")
