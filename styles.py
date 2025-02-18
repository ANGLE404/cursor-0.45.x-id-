from colorama import Fore, Style, init
import shutil
import time
import sys

# 初始化 colorama
init()

# 获取终端大小
TERM_WIDTH = shutil.get_terminal_size().columns

class Colors:
    """统一的颜色方案"""
    PRIMARY = Fore.CYAN
    SUCCESS = Fore.GREEN
    ERROR = Fore.RED
    WARNING = Fore.YELLOW
    INFO = Fore.BLUE
    TITLE = Fore.MAGENTA
    RESET = Style.RESET_ALL
    BRIGHT = Style.BRIGHT

class Emoji:
    """统一的表情符号"""
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    DONE = "🎉"
    KEY = "🔑"
    MAIL = "📧"
    BROWSER = "🌐"
    ROCKET = "🚀"
    STAR = "⭐"
    FILE = "📄"
    GEAR = "⚙️"
    LOCK = "🔒"
    UNLOCK = "🔓"

class BorderStyles:
    """边框样式"""
    SINGLE = {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"}
    DOUBLE = {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"}
    ROUND = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"}

class SpecialEffects:
    """特效类"""
    @staticmethod
    def typing_print(text: str, delay: float = 0.001):
        """打字机效果"""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

    @staticmethod
    def loading_spinner(text: str, duration: float = 0.2):
        """加载动画"""
        spinners = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        start_time = time.time()
        i = 0
        while time.time() - start_time < duration:
            print(f"\r{Colors.INFO}{spinners[i % len(spinners)]} {text}...{Colors.RESET}", end="")
            time.sleep(0.02)
            i += 1
        print()

    @staticmethod
    def progress_bar(progress: float, text: str = "", width: int = 40):
        """进度条"""
        filled = int(width * progress)
        bar = '█' * filled + '░' * (width - filled)
        percentage = int(progress * 100)
        print(f"\r{Colors.INFO}{text} [{bar}] {percentage}%{Colors.RESET}", end='')
        if progress >= 1:
            print()

def print_fancy_box(text: str, style: str = "double", color: str = Colors.PRIMARY):
    """打印美化的文本框"""
    borders = getattr(BorderStyles, style.upper())
    width = len(text) + 4
    print(f"\n{color}{borders['tl']}{borders['h'] * (width-2)}{borders['tr']}")
    print(f"{borders['v']} {text} {borders['v']}")
    print(f"{borders['bl']}{borders['h'] * (width-2)}{borders['br']}{Colors.RESET}\n")

def print_title(text: str):
    """打印居中的标题"""
    padding = (TERM_WIDTH - len(text)) // 2
    print(f"\n{Colors.TITLE}{Colors.BRIGHT}{' ' * padding}{text}{Colors.RESET}\n")