import os
import shutil
import time
import psutil
import PyInstaller.__main__

def is_process_running(process_name):
    """检查进程是否在运行"""
    for proc in psutil.process_iter(['name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def safe_remove_directory(path):
    """安全地删除目录，如果失败则等待重试"""
    if not os.path.exists(path):
        return
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # 尝试删除目录
            shutil.rmtree(path, ignore_errors=True)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"删除{path}失败，等待{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                print(f"警告: 无法删除{path}目录: {e}")
                print("继续构建过程...")

def build():
    # 检查是否有相关进程在运行
    if is_process_running("Cursor Reset.exe"):
        print("请先关闭Cursor Reset程序再进行构建")
        return
    
    # 安全清理之前的构建
    print("清理旧的构建文件...")
    safe_remove_directory('build')
    safe_remove_directory('dist')
    
    # 图标路径
    icon_path = r"C:\Users\QQB\CODE\cursor-reset-main\cursor-free-vip\Hacker_News_icon-icons.com_55898.ico"
    
    print("开始打包...")
    try:
        # 使用命令行参数直接打包
        PyInstaller.__main__.run([
            'cursor45 mail 美化.py',  # 主程序
            '--name=Cursor Reset',  # 程序名称
            '--windowed',  # 无控制台
            '--clean',  # 清理临时文件
            '--noconfirm',  # 不确认覆盖
            f'--icon={icon_path}',  # 使用指定图标
            '--uac-admin',  # 请求管理员权限
            '--add-data=locales/*.json;locales',  # 添加语言文件
            '--add-data=main.py;.',  # 添加主程序
            '--add-data=cursor_register.py;.',  # 添加注册程序
            '--add-data=reset_machine_manual.py;.',  # 添加重置程序
            '--add-data=quit_cursor.py;.',  # 添加退出程序
            '--add-data=logo.py;.',  # 添加logo文件
            '--hidden-import=PyQt6',
            '--hidden-import=win32security',
            '--hidden-import=win32api',
            '--hidden-import=win32con',
            '--hidden-import=psutil',
            '--hidden-import=colorama',
            '--version-file=file_version_info.txt',  # 添加版本信息
        ])
        print("打包完成！")
        
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        return

if __name__ == "__main__":
    build()