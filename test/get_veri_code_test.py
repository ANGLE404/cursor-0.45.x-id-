from DrissionPage import ChromiumOptions, Chromium
from DrissionPage.common import Keys
import time
import re
import sys
import os


def get_extension_path():
    """获取插件路径"""
    root_dir = os.getcwd()
    extension_path = os.path.join(root_dir, "turnstilePatch")

    if hasattr(sys, "_MEIPASS"):
        print("运行在打包环境中")
        extension_path = os.path.join(sys._MEIPASS, "turnstilePatch")

    print(f"尝试加载插件路径: {extension_path}")

    if not os.path.exists(extension_path):
        raise FileNotFoundError(
            f"插件不存在: {extension_path}\n请确保 turnstilePatch 文件夹在正确位置"
        )

    return extension_path


def get_browser_options():
    co = ChromiumOptions()
    try:
        extension_path = get_extension_path()
        co.add_extension(extension_path)
    except FileNotFoundError as e:
        print(f"警告: {e}")

    co.set_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.92 Safari/537.36"
    )
    co.set_pref("credentials_enable_service", False)
    co.set_argument("--hide-crash-restore-bubble")
    co.auto_port()

    # Mac 系统特殊处理
    if sys.platform == "darwin":
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")

    return co


def get_veri_code(username):
    # 使用相同的浏览器配置
    co = get_browser_options()
    browser = Chromium(co)
    code = None

    try:
        # 获取当前标签页
        tab = browser.latest_tab
        tab.run_js("try { turnstile.reset() } catch(e) { }")

        # 打开临时邮箱网站
        tab.get("https://tempmail.plus/zh")
        time.sleep(2)

        # 设置邮箱用户名
        while True:
            if tab.ele("@id=pre_button"):
                # 点击输入框
                tab.actions.click("@id=pre_button")
                time.sleep(1)
                # 删除之前的内容
                tab.run_js('document.getElementById("pre_button").value = ""')

                # 输入新用户名并回车
                tab.actions.input(username).key_down(Keys.ENTER).key_up(Keys.ENTER)
                break
            time.sleep(1)

        # 等待并获取新邮件
        while True:
            new_mail = tab.ele("@class=mail")
            if new_mail:
                if new_mail.text:
                    print("最新的邮件：", new_mail.text)
                    tab.actions.click("@class=mail")
                    break
                else:
                    print(new_mail)
                    break
            time.sleep(1)

        # 提取验证码
        if tab.ele("@class=overflow-auto mb-20"):
            email_content = tab.ele("@class=overflow-auto mb-20").text
            verification_code = re.search(
                r"verification code is (\d{6})", email_content
            )
            if verification_code:
                code = verification_code.group(1)
                print("验证码：", code)
            else:
                print("未找到验证码")

        # 删除邮件
        if tab.ele("@id=delete_mail"):
            tab.actions.click("@id=delete_mail")
            time.sleep(1)

        if tab.ele("@id=confirm_mail"):
            tab.actions.click("@id=confirm_mail")
            print("删除邮件")

    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        browser.quit()

    return code


# 测试运行
if __name__ == "__main__":
    test_username = "test_user"  # 替换为你要测试的用户名
    code = get_veri_code(test_username)
    print(f"获取到的验证码: {code}")
