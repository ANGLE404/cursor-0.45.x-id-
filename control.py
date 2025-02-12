import time
import random
import os
from colorama import Fore, Style, init

# 初始化colorama
init()

# 定义emoji常量
EMOJI = {
    'MAIL': '📧',
    'REFRESH': '🔄',
    'SUCCESS': '✅',
    'ERROR': '❌',
    'INFO': 'ℹ️',
    'CODE': '📱'
}

class BrowserControl:
    def __init__(self, browser, translator=None):
        self.browser = browser
        self.translator = translator  # 保存translator
        self.sign_up_url = "https://authenticator.cursor.sh/sign-up"
        self.current_tab = None  # 当前标签页
        self.signup_tab = None   # 注册标签页
        self.email_tab = None    # 邮箱标签页

    def create_new_tab(self):
        """创建新标签页"""
        try:
            # 保存当前标签页
            self.current_tab = self.browser
            
            # 创建新的浏览器实例
            from browser import BrowserManager
            browser_manager = BrowserManager()
            new_browser = browser_manager.init_browser()
            
            # 保存新标签页
            self.signup_tab = new_browser
            
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.create_new_tab_success')}{Style.RESET_ALL}")
            return new_browser
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.create_new_tab_failed', error=str(e))}{Style.RESET_ALL}")
            return None

    def switch_to_tab(self, browser):
        """切换到指定浏览器窗口"""
        try:
            self.browser = browser
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.switch_tab_success')}{Style.RESET_ALL}")
            return True
        except Exception as e:  
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.switch_tab_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def get_current_tab(self):
        """获取当前标签页"""
        return self.browser

    def generate_new_email(self):
        """点击新的按钮生成新邮箱"""
        try:
            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('control.generate_email')}...{Style.RESET_ALL}")
            new_button = self.browser.ele('xpath://button[contains(@class, "egenbut")]')
            if new_button:
                new_button.click()
                time.sleep(1)  # 等待生成
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.generate_email_success')}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.generate_email_failed')}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.browser_error', error=str(e))}{Style.RESET_ALL}")
            return False

    def select_email_domain(self, domain_index=None):
        """选择邮箱域名，如果不指定index则随机选择"""
        try:
            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('control.select_email_domain')}...{Style.RESET_ALL}")
            
            # 读取黑名单域名
            blacklist = []
            try:
                with open('blacklist.txt', 'r', encoding='utf-8') as f:
                    blacklist = [line.strip().lower() for line in f if line.strip()]
            except FileNotFoundError:
                # 如果文件不存在，创建一个包含已知黑名单域名的文件
                with open('blacklist.txt', 'w', encoding='utf-8') as f:
                    f.write("fr.nf\nyopmail.com\n1s.fr\nfr.cr")
                blacklist = ["fr.nf", "yopmail.com", "1s.fr", "fr.cr"]
            
            # 找到下拉框
            select_element = self.browser.ele('xpath://select[@id="seldom"]')
            if select_element:
                # 获取所有选项
                all_options = []
                new_options = self.browser.eles('xpath://select[@id="seldom"]/optgroup[@label="-- 新的 --"]/option')
                other_options = self.browser.eles('xpath://select[@id="seldom"]/optgroup[@label="-- 其他 --"]/option')
                all_options.extend(new_options)
                all_options.extend(other_options)
                
                if all_options:
                    max_attempts = 5
                    attempt = 0
                    
                    while attempt < max_attempts:
                        if domain_index is None:
                            domain_index = random.randint(0, len(all_options) - 1)
                        
                        if domain_index < len(all_options):
                            selected_domain = all_options[domain_index].text.lower()
                            
                            # 检查域名是否在黑名单中
                            is_blacklisted = False
                            for blocked_domain in blacklist:
                                if blocked_domain in selected_domain:
                                    print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('control.blocked_domain', domain=blocked_domain)}{Style.RESET_ALL}")
                                    domain_index = None
                                    attempt += 1
                                    is_blacklisted = True
                                    break
                            
                            if is_blacklisted:
                                continue
                            
                            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('control.select_email_domain')}: {selected_domain}{Style.RESET_ALL}")
                            
                            # 点击选择
                            all_options[domain_index].click()
                            time.sleep(1)
                            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.select_email_domain_success')}{Style.RESET_ALL}")
                            return True
                        
                        attempt += 1
                    
                    print(f"{Fore.RED}{EMOJI['ERROR']} 无法找到可用的域名{Style.RESET_ALL}")
                    return False
                
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.no_available_domain_options', count=len(all_options))}{Style.RESET_ALL}")
                return False
            else:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.no_domain_select_box')}{Style.RESET_ALL}")
                return False
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.select_email_domain_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def wait_for_page_load(self, seconds=2):
        """等待页面加载"""
        time.sleep(seconds)

    def navigate_to(self, url):
        """导航到指定URL"""
        try:
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('control.navigate_to', url=url)}...{Style.RESET_ALL}")
            self.browser.get(url)
            self.wait_for_page_load()
            return True
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.browser_error', error=str(e))}{Style.RESET_ALL}")
            return False

    def copy_and_get_email(self):
        """获取邮箱地址"""
        try:
            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('control.generate_email')}...{Style.RESET_ALL}")
            
            # 等待元素加载
            time.sleep(1)
            
            # 获取邮箱名称
            try:
                email_div = self.browser.ele('xpath://div[@class="segen"]//div[contains(@style, "color: #e5e5e5")]')
                if email_div:
                    email_name = email_div.text.split()[0]
                    print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('control.get_email_name')}: {email_name}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.get_email_name_failed')}{Style.RESET_ALL}")
                    return None
            except Exception as e:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.get_email_name_failed', error=str(e))}{Style.RESET_ALL}")
                return None
            
            # 直接使用上一步选择的域名
            try:
                domain = self.browser.ele('xpath://select[@id="seldom"]').value
                if not domain:  # 如果获取不到value，尝试获取选中的选项文本
                    selected_option = self.browser.ele('xpath://select[@id="seldom"]/option[1]')
                    domain = selected_option.text if selected_option else "@yopmail.com"  # 使用默认域名作为后备
            except:
                domain = "@yopmail.com"  # 如果出错，使用默认域名
            
            # 组合完整邮箱地址
            full_email = f"{email_name}{domain}"
            print(f"{Fore.GREEN}{EMOJI['MAIL']} {self.translator.get('control.get_email_address')}: {full_email}{Style.RESET_ALL}")
            return full_email
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.get_email_address_failed', error=str(e))}{Style.RESET_ALL}")
            return None 

    def view_mailbox(self):
        """点击查看邮箱按钮"""
        try:
            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('control.enter_mailbox')}...{Style.RESET_ALL}")
            view_button = self.browser.ele('xpath://button[contains(@class, "egenbut") and contains(.//span, "查看邮箱")]')
            if view_button:
                view_button.click()
                time.sleep(2)  # 等待页面加载
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.enter_mailbox_success')}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.no_view_mailbox_button')}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.enter_mailbox_failed', error=str(e))}{Style.RESET_ALL}")
            return False 

    def refresh_mailbox(self):
        """刷新邮箱获取最新信息"""
        try:
            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('control.refresh_mailbox')}...{Style.RESET_ALL}")
            refresh_button = self.browser.ele('xpath://button[@id="refresh"]')
            if refresh_button:
                refresh_button.click()
                time.sleep(2)  # 等待刷新完成
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.refresh_mailbox_success')}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.no_refresh_button')}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.refresh_mailbox_failed', error=str(e))}{Style.RESET_ALL}")
            return False 


    def get_verification_code(self):
        """从邮件中获取验证码"""
        try:
            # 尝试所有可能的样式组合
            selectors = [
                # 新样式
                'xpath://div[contains(@style, "font-family:-apple-system") and contains(@style, "font-size:28px") and contains(@style, "letter-spacing:2px") and contains(@style, "color:#202020")]',
                # 带行高的样式
                'xpath://div[contains(@style, "font-size:28px") and contains(@style, "letter-spacing:2px") and contains(@style, "line-height:30px")]',
                # rgba 颜色样式
                'xpath://div[contains(@style, "font-size: 28px") and contains(@style, "letter-spacing: 2px") and contains(@style, "color: rgba(32, 32, 32, 1)")]',
                # 宽松样式
                'xpath://div[contains(@style, "font-size:28px") and contains(@style, "letter-spacing:2px")]'
            ]
            
            # 依次尝试每个选择器
            for selector in selectors:
                code_div = self.browser.ele(selector)
                if code_div:
                    verification_code = code_div.text.strip()
                    if verification_code.isdigit() and len(verification_code) == 6:
                        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.found_verification_code')}: {verification_code}{Style.RESET_ALL}")
                        return verification_code
                    
            print(f"{Fore.YELLOW}{EMOJI['ERROR']} {self.translator.get('control.no_valid_verification_code')}{Style.RESET_ALL}")
            return None
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.get_verification_code_error', error=str(e))}{Style.RESET_ALL}")
            return None

    def fill_verification_code(self, code):
        """填写验证码"""
        try:
            if not code or len(code) != 6:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.verification_code_format_error')}{Style.RESET_ALL}")
                return False

            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('control.fill_verification_code')}...{Style.RESET_ALL}")
            
            # 记住当前标签页（邮箱页面）
            email_tab = self.browser
            
            # 切换回注册页面标签
            self.switch_to_tab(self.signup_tab)
            time.sleep(1)
            
            # 输入验证码
            for digit in code:
                self.browser.actions.input(digit)
                time.sleep(random.uniform(0.1, 0.3))
            
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.verification_code_filled')}{Style.RESET_ALL}")
            
            # 等待页面加载和登录完成
            print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('control.wait_for_login')}...{Style.RESET_ALL}")
            time.sleep(5)
            
            # 先访问登录页面确保登录状态
            login_url = "https://authenticator.cursor.sh"
            self.browser.get(login_url)
            time.sleep(3)  # 增加等待时间
            
            # 获取cookies（第一次尝试）
            token = self.get_cursor_session_token()
            if not token:
                print(f"{Fore.YELLOW}{EMOJI['ERROR']} {self.translator.get('control.get_token_failed')}...{Style.RESET_ALL}")
                time.sleep(3)
                token = self.get_cursor_session_token()
            
            if token:
                self.save_token_to_file(token)
                
                # 获取到token后再访问设置页面
                settings_url = "https://www.cursor.com/settings"
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('control.get_account_info')}...{Style.RESET_ALL}")
                self.browser.get(settings_url)
                time.sleep(2)
                
                # 获取账户额度信息
                try:
                    usage_selector = (
                        "css:div.col-span-2 > div > div > div > div > "
                        "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
                        "span.font-mono.text-sm\\/\\[0\\.875rem\\]"
                    )
                    usage_ele = self.browser.ele(usage_selector)
                    if usage_ele:
                        usage_info = usage_ele.text
                        total_usage = usage_info.split("/")[-1].strip()
                        print(f"{Fore.GREEN}{EMOJI['INFO']} {self.translator.get('control.account_usage_limit')}: {total_usage}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.get_account_usage_failed', error=str(e))}{Style.RESET_ALL}")
            
            # 切换回邮箱页面
            self.switch_to_tab(email_tab)
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.fill_verification_code_failed', error=str(e))}{Style.RESET_ALL}")
            return False 

    def check_and_click_turnstile(self):
        """检查并点击 Turnstile 验证框"""
        try:
            # 等待验证框出现
            time.sleep(1)
            
            # 查找验证框
            verify_checkbox = self.browser.ele('xpath://label[contains(@class, "cb-lb")]//input[@type="checkbox"]')
            if verify_checkbox:
                print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('control.find_turnstile_verification_box')}...{Style.RESET_ALL}")
                verify_checkbox.click()
                time.sleep(2)  # 等待验证完成
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.clicked_turnstile_verification_box')}{Style.RESET_ALL}")
                return True
            return False
        except Exception as e:
            print(f"{Fore.YELLOW}{EMOJI['ERROR']} {self.translator.get('control.check_and_click_turnstile_failed', error=str(e))}{Style.RESET_ALL}")
            return False 

    def get_cursor_session_token(self, max_attempts=3, retry_interval=2):
        """获取Cursor会话token"""
        print(f"{Fore.CYAN}{EMOJI['INFO']} {self.translator.get('control.get_cursor_session_token')}...{Style.RESET_ALL}")
        attempts = 0

        while attempts < max_attempts:
            try:
                # 直接从浏览器对象获取cookies
                all_cookies = self.browser.get_cookies()
                
                # 遍历查找目标cookie
                for cookie in all_cookies:
                    if cookie.get("name") == "WorkosCursorSessionToken":
                        token = cookie["value"].split("%3A%3A")[1]
                        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.get_cursor_session_token_success')}: {token}{Style.RESET_ALL}")
                        return token

                attempts += 1
                if attempts < max_attempts:
                    print(f"{Fore.YELLOW}{EMOJI['ERROR']} {self.translator.get('control.get_cursor_session_token_failed', attempts=attempts, retry_interval=retry_interval)}...{Style.RESET_ALL}")
                    time.sleep(retry_interval)
                else:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.reach_max_attempts', max_attempts=max_attempts)}{Style.RESET_ALL}")

            except Exception as e:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.get_cookie_failed', error=str(e))}{Style.RESET_ALL}")
                attempts += 1
                if attempts < max_attempts:
                    print(f"{Fore.YELLOW}{EMOJI['ERROR']} {self.translator.get('control.will_retry_in', retry_interval=retry_interval)}...{Style.RESET_ALL}")
                    time.sleep(retry_interval)

        return None

    def save_token_to_file(self, token):
        """保存token到文件"""
        try:
            with open('cursor_tokens.txt', 'a', encoding='utf-8') as f:
                f.write(f"Token: {token}\n")
                f.write("-" * 50 + "\n")
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('control.token_saved_to_file')}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('control.save_token_failed', error=str(e))}{Style.RESET_ALL}") 