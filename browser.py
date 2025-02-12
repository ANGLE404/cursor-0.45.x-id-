from DrissionPage import ChromiumOptions, ChromiumPage
import sys
import os
import logging
import random


class BrowserManager:
    def __init__(self, noheader=False):
        self.browser = None
        self.noheader = noheader

    def init_browser(self):
        """初始化浏览器"""
        co = self._get_browser_options()
        
        # 如果设置了 noheader，添加相应的参数
        if self.noheader:
            co.set_argument('--headless=new')
            
        self.browser = ChromiumPage(co)
        return self.browser

    def _get_browser_options(self):
        """获取浏览器配置"""
        co = ChromiumOptions()
        try:
            extension_path = self._get_extension_path()
            co.add_extension(extension_path)
            co.set_argument("--allow-extensions-in-incognito")

            extension_block_path = self.get_extension_block()
            co.add_extension(extension_block_path)
            co.set_argument("--allow-extensions-in-incognito")

            extension_recaptcha_path = self.get_extension_recaptcha()
            co.add_extension(extension_recaptcha_path)
            co.set_argument("--allow-extensions-in-incognito")

        except FileNotFoundError as e:
            logging.warning(f"警告: {e}")

        # 设置更真实的用户代理
        co.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 基本设置
        co.set_pref("credentials_enable_service", False)
        co.set_pref("profile.password_manager_enabled", False)
        
        # 禁用自动化标志
        co.set_pref("useAutomationExtension", False)
        co.set_pref("excludeSwitches", ["enable-automation"])
        
        # WebGL 和 GPU 设置
        co.set_pref("webgl.disabled", False)
        co.set_pref("webgl.enable_webgl2", True)
        
        # 设置语言和地区
        co.set_pref("intl.accept_languages", "en-US,en")
        
        # 基本命令行参数
        co.set_argument("--disable-blink-features=AutomationControlled")
        co.set_argument("--hide-crash-restore-bubble")
        co.set_argument("--no-first-run")
        co.set_argument("--no-default-browser-check")
        co.set_argument("--disable-popup-blocking")
        
        # 性能和稳定性参数
        co.set_argument("--disable-dev-shm-usage")
        co.set_argument("--disable-gpu")
        co.set_argument("--no-sandbox")
        co.set_argument("--ignore-certificate-errors")
        
        # WebGL 相关参数
        co.set_argument("--use-gl=swiftshader")
        co.set_argument("--enable-webgl")
        
        # 随机端口
        co.auto_port()

        # 系统特定设置
        if sys.platform == "darwin":  # macOS
            co.set_argument("--disable-gpu")
            co.set_argument("--no-sandbox")
        elif sys.platform == "win32":  # Windows
            co.set_argument("--disable-software-rasterizer")


        # 设置窗口大小
        window_width = random.randint(1024, 1920)
        window_height = random.randint(768, 1080)
        co.set_argument(f"--window-size={window_width},{window_height}")

        return co

    def _get_extension_path(self):
        """获取插件路径"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "turnstilePatch")

        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "turnstilePatch")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")

        return extension_path
    
    def get_extension_block(self):
        """获取插件路径"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "uBlock0.chromium")
        
        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "uBlock0.chromium")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")

        return extension_path

    def get_extension_recaptcha(self):
        """获取插件路径"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "recaptchaPatch")

        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "recaptchaPatch")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")

        return extension_path

    def quit(self):
        """关闭浏览器"""
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass