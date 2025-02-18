from colorama import Fore, Style, init, Back
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

class RichColors:
    """增强的颜色方案"""
    # 前景色
    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    
    # 背景色
    BG_BLACK = Back.BLACK
    BG_RED = Back.RED
    BG_GREEN = Back.GREEN
    BG_YELLOW = Back.YELLOW
    BG_BLUE = Back.BLUE
    BG_MAGENTA = Back.MAGENTA
    BG_CYAN = Back.CYAN
    BG_WHITE = Back.WHITE
    
    # 样式
    BRIGHT = Style.BRIGHT
    DIM = Style.DIM
    NORMAL = Style.NORMAL
    
    @staticmethod
    def combine(fore=None, back=None, style=None):
        """组合多种颜色效果"""
        result = ""
        if fore: result += fore
        if back: result += back  
        if style: result += style
        return result
    
    @staticmethod
    def rainbow_text(text):
        """创建彩虹文字效果"""
        colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
        result = ""
        for i, char in enumerate(text):
            result += colors[i % len(colors)] + char
        return result + Style.RESET_ALL

    @staticmethod
    def gradient_text(text, start_color, end_color):
        """创建渐变文字效果(简单实现)"""
        result = ""
        for i, char in enumerate(text):
            weight = i / len(text)
            if start_color == Fore.RED and end_color == Fore.BLUE:
                color = Fore.MAGENTA if weight > 0.5 else Fore.RED
            elif start_color == Fore.GREEN and end_color == Fore.YELLOW:
                color = Fore.YELLOW if weight > 0.5 else Fore.GREEN
            else:
                color = start_color
            result += color + char
        return result + Style.RESET_ALL

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

def print_rainbow_box(text: str, style: str = "double"):
    """打印彩虹边框的文本框"""
    borders = getattr(BorderStyles, style.upper())
    width = len(text) + 4
    print(f"\n{RichColors.rainbow_text(borders['tl'] + borders['h'] * (width-2) + borders['tr'])}")
    print(f"{RichColors.combine(Fore.CYAN)}{borders['v']}{Style.RESET_ALL} {text} {RichColors.combine(Fore.CYAN)}{borders['v']}{Style.RESET_ALL}")
    print(f"{RichColors.rainbow_text(borders['bl'] + borders['h'] * (width-2) + borders['br'])}\n")