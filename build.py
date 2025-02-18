import warnings
import os
import platform
import subprocess
import time
import threading

# 忽略特定的SyntaxWarning
warnings.filterwarnings("ignore", category=SyntaxWarning, module="DrissionPage")

CURSOR_LOGO = """
   ██████╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ 
  ██╔════╝██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗
  ██║     ██║   ██║██████╔╝███████╗██║   ██║██████╔╝
  ██║     ██║   ██║██╔══██╗╚════██║██║   ██║██╔══██╗
  ╚██████╗╚██████╔╝██║  ██║███████║╚██████╔╝██║  ██║
   ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
"""


class LoadingAnimation:
    def __init__(self):
        self.is_running = False
        self.animation_thread = None

    def start(self, message="Building"):
        self.is_running = True
        self.animation_thread = threading.Thread(target=self._animate, args=(message,))
        self.animation_thread.start()

    def stop(self):
        self.is_running = False
        if self.animation_thread:
            self.animation_thread.join()
        print("\r" + " " * 70 + "\r", end="", flush=True)  # 清除行

    def _animate(self, message):
        animation = "|/-\\"
        idx = 0
        while self.is_running:
            print(f"\r{message} {animation[idx % len(animation)]}", end="", flush=True)
            idx += 1
            time.sleep(0.1)


def print_logo():
    print("\033[96m" + CURSOR_LOGO + "\033[0m")
    print("\033[93m" + "Building Cursor Keep Alive...".center(56) + "\033[0m\n")


def progress_bar(progress, total, prefix="", length=50):
    filled = int(length * progress // total)
    bar = "█" * filled + "░" * (length - filled)
    percent = f"{100 * progress / total:.1f}"
    print(f"\r{prefix} |{bar}| {percent}% Complete", end="", flush=True)
    if progress == total:
        print()


def simulate_progress(message, duration=1.0, steps=20):
    print(f"\033[94m{message}\033[0m")
    for i in range(steps + 1):
        time.sleep(duration / steps)
        progress_bar(i, steps, prefix="Progress:", length=40)


def filter_output(output):
    """重要信息过滤"""
    if not output:
        return ""
    important_lines = []
    for line in output.split("\n"):
        # 只保留包含特定关键词的行
        if any(
            keyword in line.lower()
            for keyword in ["error:", "failed:", "completed", "directory:"]
        ):
            important_lines.append(line)
    return "\n".join(important_lines)


def build():
    # 清屏
    os.system("cls" if platform.system().lower() == "windows" else "clear")

    # 打印logo
    print_logo()

    system = platform.system().lower()
    
    # 修改spec文件路径,使用cursor_reset.spec
    spec_file = "cursor_reset.spec"
    
    if not os.path.exists(spec_file):
        print(f"\033[91m错误: 找不到spec文件 {spec_file}\033[0m")
        return

    output_dir = f"dist/{system if system != 'darwin' else 'mac'}"

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    simulate_progress("创建输出目录...", 0.5)

    # 运行PyInstaller命令 - 移除不允许的选项
    pyinstaller_command = [
        "pyinstaller",
        spec_file,
        "--distpath", output_dir,
        "--workpath", f"build/{system}",
        "--noconfirm",
        "--clean"
    ]


    loading = LoadingAnimation()
    try:
        simulate_progress("运行PyInstaller...", 2.0)
        loading.start("正在打包...")
        result = subprocess.run(
            pyinstaller_command,
            check=True,
            capture_output=True,
            text=True
        )
        loading.stop()

        if result.stderr:
            filtered_errors = filter_output(result.stderr)
            if filtered_errors:
                print("\033[93m打包警告/错误:\033[0m")
                print(filtered_errors)

    except subprocess.CalledProcessError as e:
        loading.stop()
        print(f"\033[91m打包失败,错误码: {e.returncode}\033[0m")
        if e.stderr:
            print("\033[91m错误详情:\033[0m")
            print(e.stderr)
        return
    except FileNotFoundError:
        loading.stop()
        print(
            "\033[91m错误: 请确保PyInstaller已安装 (pip install pyinstaller)\033[0m"
        )
        return
    except KeyboardInterrupt:
        loading.stop()
        print("\n\033[91m打包已被用户取消\033[0m")
        return
    finally:
        loading.stop()

    # 复制配置文件
    if os.path.exists("config.ini"):
        simulate_progress("复制配置文件...", 0.5)
        if system == "windows":
            subprocess.run(
                ["copy", "config.ini", f"{output_dir}\\config.ini"], shell=True
            )
        else:
            subprocess.run(["cp", "config.ini", f"{output_dir}/config.ini"])

    # 复制VIP激活脚本
    if os.path.exists("cursor_pro_keep_alive.py"):
        simulate_progress("复制VIP激活脚本...", 0.5)
        if system == "windows":
            subprocess.run(
                ["copy", "cursor_pro_keep_alive.py", f"{output_dir}\\cursor_pro_keep_alive.py"], 
                shell=True
            )
        else:
            subprocess.run(
                ["cp", "cursor_pro_keep_alive.py", f"{output_dir}/cursor_pro_keep_alive.py"]
            )

    print(
        f"\n\033[92m打包完成! 输出目录: {output_dir}\033[0m"
    )


if __name__ == "__main__":
    build()
