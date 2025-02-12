import sys
import os
import json
import uuid
import shutil
import logging
import win32security
import ntsecuritycon as con
import win32api
import win32con
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QProgressBar,
                            QTextEdit, QMessageBox, QFileDialog, QTabWidget,
                            QGroupBox, QCheckBox, QSpinBox, QLineEdit)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, 
                         QPropertyAnimation, QParallelAnimationGroup, 
                         QSequentialAnimationGroup, QEasingCurve, 
                         QPoint, QRect, QPointF,
                         pyqtProperty as Property)
from PyQt6.QtGui import QIcon, QFont, QPainter, QColor, QPainterPath

import time
import subprocess
import stat
import random
from math import sin, cos, pi, log
from main import translator  # 从main.py导入translator实例

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IDGenerator:
    @staticmethod
    def generate_machine_id():
        """生成64位随机ID"""
        return uuid.uuid4().hex + uuid.uuid4().hex
    
    @staticmethod
    def generate_mac_machine_id():
        """生成类似macMachineId的格式"""
        template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
        result = ""
        for char in template:
            if char in ['x', 'y']:
                r = uuid.uuid4().int & 0xF
                v = r if char == 'x' else (r & 0x3) | 0x8
                result += hex(v)[2:]
            else:
                result += char
        return result
    
    @staticmethod
    def generate_sqm_id():
        """生成sqmId"""
        return "{" + str(uuid.uuid4()).upper() + "}"

class SystemOperator:
    def __init__(self):
        self.is_windows = sys.platform.startswith('win')
        self.home_dir = Path.home()
        
    def backup_ids(self):
        """备份当前ID"""
        backup_dir = self.home_dir / "CursorReset_Backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        counter = 0
        
        if self.is_windows:
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\Microsoft\Cryptography",
                                   0, winreg.KEY_READ)
                machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                winreg.CloseKey(key)
                
                backup_file = backup_dir / f"MachineGuid_{timestamp}.txt"
                while backup_file.exists():
                    counter += 1
                    backup_file = backup_dir / f"MachineGuid_{timestamp}_{counter}.txt"
                
                backup_file.write_text(machine_guid)
                logger.info(f"Windows MachineGuid backed up to {backup_file}")
            except Exception as e:
                logger.error(f"Failed to backup Windows MachineGuid: {e}")
                raise
        else:
            try:
                uuid_file = "/var/root/Library/Preferences/SystemConfiguration/com.apple.platform.uuid.plist"
                if os.path.exists(uuid_file):
                    backup_file = backup_dir / f"PlatformUUID_{timestamp}.plist"
                    shutil.copy2(uuid_file, backup_file)
                    logger.info(f"macOS Platform UUID backed up to {backup_file}")
            except Exception as e:
                logger.error(f"Failed to backup macOS Platform UUID: {e}")
                raise

class ResetWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def run(self):
        try:
            self.status.emit("开始重置...")
            self.progress.emit(10)
            
            # 检查Cursor进程
            self.check_cursor_process()
            self.progress.emit(20)
            
            # 备份当前配置
            self.status.emit("备份当前配置...")
            self.backup_storage_json()
            system_op = SystemOperator()
            system_op.backup_ids()
            self.progress.emit(40)
            
            # 生成新ID
            self.status.emit("生成新ID...")
            id_gen = IDGenerator()
            self.new_ids = {
                'machineId': id_gen.generate_machine_id(),
                'macMachineId': id_gen.generate_mac_machine_id(),
                'devDeviceId': str(uuid.uuid4()),
                'sqmId': id_gen.generate_sqm_id()
            }
            self.progress.emit(60)
            
            # 更新配置文件
            self.status.emit("更新配置文件...")
            self.update_storage_json(self.new_ids)
            self.progress.emit(80)
            
            # 更新系统ID
            self.status.emit("更新系统ID...")
            self.update_system_ids(self.new_ids)
            self.progress.emit(100)
            
            self.finished.emit(True, "重置完成!")
            
        except Exception as e:
            logger.error(f"Reset failed: {e}")
            self.finished.emit(False, f"重置失败: {str(e)}")
    
    def check_cursor_process(self):
        """检查Cursor进程是否在运行"""
        self.status.emit("检查Cursor进程...")
        try:
            import psutil
            cursor_processes = []
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == 'cursor.exe':
                        cursor_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if cursor_processes:
                # 尝试正常关闭
                for proc in cursor_processes:
                    try:
                        proc.terminate()
                    except psutil.NoSuchProcess:
                        continue
                
                # 等待进程结束
                psutil.wait_procs(cursor_processes, timeout=3)
                
                # 检查是否还有残留进程
                for proc in cursor_processes:
                    if proc.is_running():
                        try:
                            proc.kill()
                        except psutil.NoSuchProcess:
                            continue
                
                time.sleep(1)  # 确保进程完全退出
                
                # 最后检查
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() == 'cursor.exe':
                        raise RuntimeError("无法完全关闭Cursor进程，请手动关闭后重试")
            
            logger.info("Cursor进程检查完成")
            
        except Exception as e:
            logger.error(f"检查Cursor进程失败: {e}")
            raise

    def update_storage_json(self, new_ids):
        """更新storage.json配置文件"""
        try:
            storage_path = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "globalStorage" / "storage.json"
            if not storage_path.exists():
                raise FileNotFoundError(f"找不到storage.json文件: {storage_path}")
            
            # 保存原始文件属性
            original_attributes = os.stat(storage_path)
            
            # 移除只读属性
            os.chmod(storage_path, original_attributes.st_mode | stat.S_IWRITE)
            
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 更新ID
                data["telemetry.machineId"] = new_ids['machineId']
                data["telemetry.macMachineId"] = new_ids['macMachineId']
                data["telemetry.devDeviceId"] = new_ids['devDeviceId']
                data["telemetry.sqmId"] = new_ids['sqmId']
                
                # 写入新配置
                with open(storage_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # 恢复原始文件属性
                os.chmod(storage_path, original_attributes.st_mode)
                logger.info("storage.json更新成功")
                
            except Exception as e:
                # 发生错误时恢复文件属性
                os.chmod(storage_path, original_attributes.st_mode)
                raise e
            
        except Exception as e:
            logger.error(f"更新storage.json失败: {e}")
            raise
    
    def update_system_ids(self, new_ids):
        """更新系统级别的ID"""
        self.status.emit("更新系统ID...")
        
        if sys.platform.startswith('win'):
            import winreg
            try:
                # 更新MachineGuid
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\Microsoft\Cryptography",
                                   0, winreg.KEY_WRITE)
                new_guid = str(uuid.uuid4())
                winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, new_guid)
                winreg.CloseKey(key)
                logger.info("Windows MachineGuid更新成功")
            except Exception as e:
                logger.error(f"更新Windows MachineGuid失败: {e}")
                raise
        else:
            try:
                uuid_file = "/var/root/Library/Preferences/SystemConfiguration/com.apple.platform.uuid.plist"
                if os.path.exists(uuid_file):
                    # 使用plutil命令更新plist文件
                    os.system(f'plutil -replace "UUID" -string "{new_ids["macMachineId"]}" "{uuid_file}"')
                    logger.info("macOS Platform UUID更新成功")
            except Exception as e:
                logger.error(f"更新macOS Platform UUID失败: {e}")
                raise

    def backup_storage_json(self):
        """备份storage.json文件"""
        try:
            if sys.platform.startswith('win'):
                storage_path = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "globalStorage" / "storage.json"
            else:
                storage_path = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "storage.json"
            
            if storage_path.exists():
                backup_dir = Path.home() / "CursorReset_Backups" / "storage_json"
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"storage_{timestamp}.json"
                counter = 0
                
                while backup_file.exists():
                    counter += 1
                    backup_file = backup_dir / f"storage_{timestamp}_{counter}.json"
                
                shutil.copy2(storage_path, backup_file)
                logger.info(f"storage.json已备份到: {backup_file}")
                return True
        except Exception as e:
            logger.error(f"备份storage.json失败: {e}")
            return False

    def start_cursor(self):
        """启动Cursor"""
        try:
            if sys.platform.startswith('win'):
                cursor_path = Path(os.getenv('LOCALAPPDATA')) / "Programs" / "Cursor" / "Cursor.exe"
                if cursor_path.exists():
                    subprocess.Popen([str(cursor_path)])
                    logger.info("已启动Cursor")
                    return True
            else:
                subprocess.Popen(['open', '-a', 'Cursor'])
                logger.info("已启动Cursor")
                return True
        except Exception as e:
            logger.error(f"启动Cursor失败: {e}")
            return False

class HeartParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.uniform(1, 3)  # 使用 uniform 代替 randint
        self.life = 1.0
        # 使用紫罗兰色作为基础颜色
        self.color = QColor("#9B4DE3")
        
        # 修改力的计算方式，使用 aix.py 中的收缩效果
        sk_range = -1 / (((x - self.x) ** 2 + (y - self.y) ** 2) + 1)
        self.vx = random.uniform(-2, 2) * sk_range
        self.vy = random.uniform(-2, 2) * sk_range

def heart_function(t, shrink_ratio=11):
    """爱心函数生成器，使用 aix.py 中的函数"""
    x = 16 * (sin(t) ** 3)
    y = -(13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t))
    
    # 放大
    x *= shrink_ratio
    y *= shrink_ratio
    
    return x, y

class HeartShape(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 扩大显示区域
        self.resize(800, 600)  # 增加窗口大小
        
        # 设置固定大小
        self.CANVAS_WIDTH = 800  # 增加画布宽度
        self.CANVAS_HEIGHT = 600  # 增加画布高度
        self.CANVAS_CENTER_X = self.CANVAS_WIDTH / 2
        self.CANVAS_CENTER_Y = self.CANVAS_HEIGHT / 2
        self.IMAGE_ENLARGE = 13  # 增加放大比例
        
        # 初始化点集
        self.points = set()
        self.edge_points = set()
        self.inside_points = set()
        self.all_points = {}
        self.frame_count = 20
        self.current_frame = 0
        
        # 构建点集
        self.build(2000)
        
        # 计算所有帧的点
        for f in range(self.frame_count):
            self.calc(f)
        
        # 启动定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(60)  # 约30fps
        
        # 确保窗口居中显示
        if parent:
            self.move(
                (parent.width() - self.width()) // 2,
                (parent.height() - self.height()) // 2 - 50  # 稍微向上偏移
            )

    def build(self, number):
        """构建基础点集"""
        # 随机在心形曲线上找点
        for _ in range(number):
            t = random.uniform(0, 2 * pi)
            x, y = self.heart_function(t)
            x, y = self.shrink(x, y, -1000)
            self.points.add((int(x), int(y)))
        
        # 边缘扩散
        for px, py in self.points:
            for _ in range(3):
                x, y = self.scatter_inside(px, py, 0.05)
                self.edge_points.add((x, y))
        
        # 内部填充
        pt_list = list(self.points)
        for _ in range(4000):
            x, y = random.choice(pt_list)
            x, y = self.scatter_inside(x, y)
            self.inside_points.add((x, y))
    
    def heart_function(self, t, enlarge_ratio=None):
        """心形函数"""
        if enlarge_ratio is None:
            enlarge_ratio = self.IMAGE_ENLARGE
        x = 16 * (sin(t) ** 3)
        y = -(13 * cos(t) - 5 * cos(2*t) - 2 * cos(3*t) - cos(4*t))
        
        x *= enlarge_ratio
        y *= enlarge_ratio
        
        x += self.CANVAS_CENTER_X
        y += self.CANVAS_CENTER_Y
        
        return int(x), int(y)
    
    def scatter_inside(self, x, y, beta=0.15):
        """散射函数"""
        ratio_x = -beta * log(random.random())
        ratio_y = -beta * log(random.random())
        dx = ratio_x * (x - self.CANVAS_CENTER_X)
        dy = ratio_y * (y - self.CANVAS_CENTER_Y)
        return x - dx, y - dy
    
    def shrink(self, x, y, ratio):
        """收缩效果"""
        sk_range = -1 / (((x-self.CANVAS_CENTER_X) ** 2 + (y-self.CANVAS_CENTER_Y) ** 2) + 1)
        dx = ratio * sk_range * (x-self.CANVAS_CENTER_X)
        dy = ratio * sk_range * (y-self.CANVAS_CENTER_Y)
        return x - dx, y - dy
    
    def calc(self, frame):
        """计算每一帧的点集"""
        ratio = 1000 + 150 * sin(frame / 10 * pi)
        all_pts = []
        
        # 光晕效果
        halo_radius = int(4 + 3 * (1 + sin(frame / 30 * pi)))
        halo_number = int(4000 + 2000 * abs(sin(frame / 30 * pi)))
        heart_halo = set()
        
        for _ in range(halo_number):
            t = random.uniform(0, 2 * pi)
            x, y = self.heart_function(t, enlarge_ratio=11.6)
            x, y = self.shrink(x, y, halo_radius)
            if (x, y) not in heart_halo:
                heart_halo.add((x, y))
                x += random.uniform(-8, 8)
                y += random.uniform(-8, 8)
                size = random.uniform(1, 2)
                all_pts.append((x, y, size))
        
        # 主体
        for x, y in self.points:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(2, 3)
            all_pts.append((x, y, size))
        
        # 边缘
        for x, y in self.edge_points:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(1.5, 2.5)
            all_pts.append((x, y, size))
        
        # 内部
        for x, y in self.inside_points:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(1, 2)
            all_pts.append((x, y, size))
        
        self.all_points[frame] = all_pts
    
    def cal_position(self, x, y, ratio):
        """计算心跳效果下的位置"""
        bt_range = 1 / (((x-self.CANVAS_CENTER_X) ** 2 + (y-self.CANVAS_CENTER_Y) ** 2) + 1)
        dx = ratio * bt_range * (x-self.CANVAS_CENTER_X)
        dy = ratio * bt_range * (y-self.CANVAS_CENTER_Y)
        return x - dx, y - dy
    
    def update_frame(self):
        """更新当前帧"""
        self.current_frame = (self.current_frame + 1) % self.frame_count
        self.update()
    
    def paintEvent(self, event):
        """绘制当前帧"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算心跳颜色
        pulse = sin(self.current_frame / 10 * pi)
        r = max(0, min(255, 155 + int(20 * pulse)))
        g = max(0, min(255, 77 + int(20 * pulse)))
        b = max(0, min(255, 227 + int(20 * pulse)))
        color = QColor(r, g, b)
        
        # 绘制所有点
        for x, y, size in self.all_points[self.current_frame]:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), size, size)

class HeartLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__("💗", parent)
        self._opacity = 1.0
        self._scale = 1.0
        self.setStyleSheet("""
            QLabel {
                color: #F2E6FF;
                font-size: 36px;
            }
        """)
    
    def _get_opacity(self):
        return self._opacity
    
    def _set_opacity(self, value):
        self._opacity = value
        self.setStyleSheet(f"""
            QLabel {{
                color: #F2E6FF;
                font-size: 36px;
                opacity: {value};
            }}
        """)
    
    opacity = Property(float, _get_opacity, _set_opacity)

class Particle:
    """粒子特效类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, 0)
        self.size = random.uniform(2, 6)
        self.alpha = 1.0
        self.color = QColor("#9B4DE3")  # 紫色粒子
        self.life = 1.0
        
    def update(self):
        """更新粒子状态"""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # 重力
        self.life -= 0.02
        self.alpha = self.life
        self.size *= 0.97
        return self.life > 0

class ParticleEffect(QWidget):
    """粒子效果控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.particles = []
        
        # 创建动画定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16)  # ~60fps
        
    def add_particles(self, x, y, count=10):
        """添加粒子"""
        for _ in range(count):
            self.particles.append(Particle(x, y))
            
    def update_particles(self):
        """更新所有粒子"""
        self.particles = [p for p in self.particles if p.update()]
        self.update()
        
    def paintEvent(self, event):
        """绘制粒子"""
        if not self.particles:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for p in self.particles:
            p.color.setAlphaF(p.alpha)
            painter.setBrush(p.color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)

class HeartAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        
        # 设置窗口透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        
        # 初始化参数 - 将心形居中显示
        self.center_x = screen.width() // 2
        self.center_y = screen.height() // 2
        self.enlarge = 11
        
        # 点集
        self.points = set()
        self.edge_points = set()
        self.inside_points = set()
        self.all_points = {}
        self.frame = 0
        
        # 初始化点
        self.build(2000)
        
        # 动画定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(120)  # 约30fps

    def scatter_inside(self, x, y, beta=0.15):
        """散射点"""
        ratiox = -beta * log(random.random())
        ratioy = -beta * log(random.random())
        dx = ratiox * (x - self.center_x)
        dy = ratioy * (y - self.center_y)
        return x - dx, y - dy
    
    def heart_function(self, t):
        """心形函数"""
        x = 16 * (sin(t)**3)
        y = -(13 * cos(t) - 5 * cos(2*t) - 2 * cos(3*t) - cos(4*t))
        
        # 放大
        x *= self.enlarge
        y *= self.enlarge
        
        # 移到中心
        x += self.center_x
        y += self.center_y
        
        return int(x), int(y)
    
    def shrink(self, x, y, ratio):
        """收缩效果"""
        sk_range = -1 / (((x-self.center_x) ** 2 + (y-self.center_y) ** 2) + 1)
        dx = ratio * sk_range * (x-self.center_x)
        dy = ratio * sk_range * (y-self.center_y)
        return x - dx, y - dy
    
    def build(self, number):
        """构建点集"""
        # 心形曲线上的点
        for _ in range(number):
            t = random.uniform(0, 2 * pi)
            x, y = self.heart_function(t)
            x, y = self.shrink(x, y, -1000)
            self.points.add((int(x), int(y)))
        
        # 边缘点
        for px, py in self.points:
            for _ in range(3):
                x, y = self.scatter_inside(px, py, 0.05)
                self.edge_points.add((x, y))
        
        # 内部填充点
        pt_ls = list(self.points)
        for _ in range(4000):
            x, y = random.choice(pt_ls)
            x, y = self.scatter_inside(x, y)
            self.inside_points.add((x, y))
    
    def cal_position(self, x, y, ratio):
        """计算位置"""
        bt_range = 1 / (((x-self.center_x) ** 2 + (y-self.center_y) ** 2) + 1)
        dx = ratio * bt_range * (x-self.center_x)
        dy = ratio * bt_range * (y-self.center_y)
        return x - dx, y - dy
    
    def paintEvent(self, event):
        """绘制事件"""
        if not self.isVisible():
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 不再填充背景，保持透明
        
        # 心跳动画参数
        ratio = 1000 + 150 * sin(self.frame / 10 * pi)
        
        # 光晕效果
        halo_radius = int(4 + 3 * (1 + sin(self.frame / 30 * pi)))
        halo_number = int(4000 + 2000 * abs(sin(self.frame / 30 * pi)))
        heart_halo_point = set()
        
        # 颜色计算 - 添加透明度
        pulse = sin(self.frame / 10 * pi)
        r = max(0, min(255, 155 + int(20 * pulse)))
        g = max(0, min(255, 77 + int(20 * pulse)))
        b = max(0, min(255, 227 + int(20 * pulse)))
        
        # 光晕粒子 - 半透明
        halo_color = QColor(r, g, b, 128)  # 添加透明度
        for _ in range(halo_number):
            t = random.uniform(0, 2 * pi)
            x, y = self.heart_function(t)
            x, y = self.shrink(x, y, halo_radius)
            if (x, y) not in heart_halo_point:
                heart_halo_point.add((x, y))
                x += random.uniform(-8, 8)
                y += random.uniform(-8, 8)
                size = random.uniform(1, 2)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(halo_color)
                painter.drawEllipse(QPointF(x, y), size, size)
        
        # 主体颜色 - 半透明
        main_color = QColor(r, g, b, 180)  # 添加透明度
        painter.setBrush(main_color)
        
        # 主体轮廓点
        for x, y in self.points:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(2, 3)
            painter.drawEllipse(QPointF(x, y), size, size)
        
        # 边缘点
        for x, y in self.edge_points:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(1.5, 2.5)
            painter.drawEllipse(QPointF(x, y), size, size)
        
        # 内部填充点
        for x, y in self.inside_points:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(1, 2)
            painter.drawEllipse(QPointF(x, y), size, size)
        
        self.frame += 1

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cursor Reset")
        self.setMinimumSize(600, 400)
        
        # 初始化彩蛋相关变量
        self._animation_group = None
        self._easter_egg_counter = 0
        self._easter_egg_timer = QTimer(self)
        self._easter_egg_timer.timeout.connect(self._reset_easter_egg)
        self._easter_egg_labels = []
        self._easter_egg_texts = [
            "感谢使用 Cursor Reset",
            "希望能帮助到你 ❤️",
            "祝你使用愉快~"
        ]
        
        # 设置窗口标题和字体
        self.setWindowTitle("Cursor Reset")
        self.setFont(QFont("Microsoft YaHei UI", 9))  # 使用微软雅黑UI字体
        
        # 创建主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # 创建主要操作标签页
        main_tab = QWidget()
        main_layout = QVBoxLayout(main_tab)
        
        # 状态组
        status_group = QGroupBox("当前状态")
        status_layout = QVBoxLayout()
        self.status_label = QLabel(self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #F2E6FF;
                font-size: 14px;
            }
        """)
        self.status_label.setText("就绪")
        self.status_label.resize(400, 30)
        self.status_label.move(
            (self.width() - self.status_label.width()) // 2,
            50
        )
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 进度组
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel(self)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #F2E6FF;
                font-size: 14px;
            }
        """)
        self.progress_label.resize(400, 30)
        self.progress_label.move(
            (self.width() - self.progress_label.width()) // 2,
            90
        )
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 操作按钮组
        button_group = QGroupBox("操作")
        button_layout = QVBoxLayout()  # 改为垂直布局
        
        # 第一行按钮
        first_row_layout = QHBoxLayout()
        self.reset_button = QPushButton("开始重置")
        self.reset_button.setMinimumHeight(40)  # 设置最小高度
        self.reset_button.setFont(QFont('Arial', 10, QFont.Weight.Bold))  # 设置字体
        self.reset_button.clicked.connect(self.start_reset)
        first_row_layout.addWidget(self.reset_button)

        self.backup_button = QPushButton("备份当前ID")
        self.backup_button.setMinimumHeight(40)
        self.backup_button.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.backup_button.clicked.connect(self.backup_ids)
        first_row_layout.addWidget(self.backup_button)

        self.force_kill_button = QPushButton("强制关闭Cursor")
        self.force_kill_button.setMinimumHeight(40)
        self.force_kill_button.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.force_kill_button.clicked.connect(self.force_kill_cursor)
        self.force_kill_button.setObjectName("force_kill_button")
        first_row_layout.addWidget(self.force_kill_button)

        # 第二行按钮
        second_row_layout = QHBoxLayout()
        self.moemail_button = QPushButton("打开AYC404临时邮箱")
        self.moemail_button.setMinimumHeight(40)
        self.moemail_button.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.moemail_button.clicked.connect(lambda: self.open_url("https://ayc404.xyz/moe"))
        second_row_layout.addWidget(self.moemail_button)

        self.register_button = QPushButton("注册Cursor")
        self.register_button.setMinimumHeight(40)
        self.register_button.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.register_button.clicked.connect(self.register_cursor)
        second_row_layout.addWidget(self.register_button)

        # 设置按钮组的间距
        first_row_layout.setSpacing(10)  # 设置按钮之间的间距
        second_row_layout.setSpacing(10)

        # 将两行按钮添加到主布局
        button_layout.addLayout(first_row_layout)
        button_layout.addLayout(second_row_layout)
        button_group.setLayout(button_layout)
        main_layout.addWidget(button_group)
        
        # 日志组
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 添加ID显示组
        id_group = QGroupBox("ID信息")
        id_layout = QVBoxLayout()
        
        # 当前ID
        current_id_group = QGroupBox("当前ID")
        current_id_layout = QVBoxLayout()
        self.current_mac_id_label = QLabel("telemetry.macMachineId: 待读取")
        self.current_machine_id_label = QLabel("telemetry.machineId: 待读取")
        self.current_dev_id_label = QLabel("telemetry.devDeviceId: 待读取")
        self.current_sqm_id_label = QLabel("telemetry.sqmId: 待读取")
        current_id_layout.addWidget(self.current_mac_id_label)
        current_id_layout.addWidget(self.current_machine_id_label)
        current_id_layout.addWidget(self.current_dev_id_label)
        current_id_layout.addWidget(self.current_sqm_id_label)
        current_id_group.setLayout(current_id_layout)
        
        # 新ID
        new_id_group = QGroupBox("新ID")
        new_id_layout = QVBoxLayout()
        self.new_mac_id_label = QLabel("telemetry.macMachineId: 等待重置...")
        self.new_machine_id_label = QLabel("telemetry.machineId: 等待重置...")
        self.new_dev_id_label = QLabel("telemetry.devDeviceId: 等待重置...")
        self.new_sqm_id_label = QLabel("telemetry.sqmId: 等待重置...")
        new_id_layout.addWidget(self.new_mac_id_label)
        new_id_layout.addWidget(self.new_machine_id_label)
        new_id_layout.addWidget(self.new_dev_id_label)
        new_id_layout.addWidget(self.new_sqm_id_label)
        new_id_group.setLayout(new_id_layout)
        
        id_layout.addWidget(current_id_group)
        id_layout.addWidget(new_id_group)
        id_group.setLayout(id_layout)
        
        # 将ID组添加到主布局
        main_layout.addWidget(id_group)
        
        tabs.addTab(main_tab, "主要操作")
        
        # 在设置标签页添加彩蛋提示
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # 添加彩蛋提示
        easter_hint = QLabel("💗 小彩蛋：连续点击5次标题栏试试看~ 💗")
        easter_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        easter_hint.setFont(QFont("Microsoft YaHei UI", 10))
        easter_hint.setStyleSheet("""
            QLabel {
                color: #5D3F92;
                margin: 10px;
            }
        """)
        settings_layout.addWidget(easter_hint)
        self.easter_hint = easter_hint
        
        # 添加直接触发按钮
        easter_button = QPushButton("直接触发彩蛋")
        easter_button.clicked.connect(self._show_easter_egg)
        settings_layout.addWidget(easter_button)
        
        # 添加设置选项
        backup_group = QGroupBox("备份设置")
        backup_layout = QVBoxLayout()
        self.auto_backup = QCheckBox("自动备份")
        self.auto_backup.setChecked(True)
        backup_layout.addWidget(self.auto_backup)
        backup_group.setLayout(backup_layout)
        settings_layout.addWidget(backup_group)
        
        # 在设置标签页添加主题切换
        theme_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout()
        
        # 主题模式选择
        self.theme_mode = QCheckBox("使用深色主题")
        self.theme_mode.setChecked(self.is_dark_mode())  # 默认跟随系统
        self.theme_mode.stateChanged.connect(self.on_theme_changed)
        
        # 系统主题跟随
        self.follow_system = QCheckBox("跟随系统主题")
        self.follow_system.setChecked(True)
        self.follow_system.stateChanged.connect(self.on_follow_system_changed)
        
        theme_layout.addWidget(self.theme_mode)
        theme_layout.addWidget(self.follow_system)
        theme_group.setLayout(theme_layout)
        settings_layout.addWidget(theme_group)
        
        tabs.addTab(settings_tab, "设置")
        
        # 添加底部版权信息
        copyright_label = QLabel("© ayc404制作 拒绝商用")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setObjectName("copyright_label")
        layout.addWidget(copyright_label)
        
        # 添加粒子效果层
        self.particle_effect = ParticleEffect(self)
        self.particle_effect.resize(self.size())
        
        # 检测系统主题
        self.update_theme()
        
        # 初始化工作线程
        self.worker = None
        
        # 读取当前ID
        self.load_current_ids()
        
        # 初始化彩蛋组件
        self.heart_widget = None
        
    def start_reset(self):
        """开始重置操作"""
        reply = QMessageBox.question(
            self, '确认', '确定要重置Cursor ID吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 先检查并关闭Cursor
            self.check_and_kill_cursor()
            time.sleep(1)  # 等待进程完全退出
            
            self.reset_button.setEnabled(False)
            self.backup_button.setEnabled(False)
            self.progress_bar.setValue(0)
            
            self.worker = ResetWorker()
            self.worker.progress.connect(self.update_progress)
            self.worker.status.connect(self.update_status)
            self.worker.finished.connect(self.reset_finished)
            self.worker.start()
    
    def backup_ids(self):
        """备份当前ID"""
        try:
            system_op = SystemOperator()
            system_op.backup_ids()
            self.log_message("备份完成")
            QMessageBox.information(self, "成功", "ID备份完成!")
        except Exception as e:
            self.log_message(f"备份失败: {e}")
            QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_status(self, text):
        """更新状态文字"""
        self.status_label.setText(text)
    
    def reset_finished(self, success, message):
        """重置完成处理"""
        self.reset_button.setEnabled(True)
        self.backup_button.setEnabled(True)
        
        if success:
            # 更新新ID显示
            if hasattr(self.worker, 'new_ids'):
                self.new_mac_id_label.setText(f"telemetry.macMachineId: {self.worker.new_ids['macMachineId']}")
                self.new_machine_id_label.setText(f"telemetry.machineId: {self.worker.new_ids['machineId']}")
                self.new_dev_id_label.setText(f"telemetry.devDeviceId: {self.worker.new_ids['devDeviceId']}")
                self.new_sqm_id_label.setText(f"telemetry.sqmId: {self.worker.new_ids['sqmId']}")
            
            QMessageBox.information(self, "成功", message)
            
            # 询问是否立即启动Cursor
            reply = QMessageBox.question(
                self, '启动Cursor', '重置完成，是否立即启动Cursor？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.start_cursor()
        else:
            QMessageBox.critical(self, "错误", message)
        
        self.log_message(message)
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def force_kill_cursor(self, show_confirm=True):
        """强制关闭Cursor进程"""
        if show_confirm:
            reply = QMessageBox.question(
                self, '确认', '确定要强制关闭Cursor吗？\n这可能导致未保存的工作丢失。',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return False
        
        try:
            if sys.platform.startswith('win'):
                os.system('taskkill /f /im cursor.exe')
            else:
                os.system('killall -9 "Cursor"')
            time.sleep(1)  # 等待进程完全退出
            return True
        except Exception as e:
            self.log_message(f"强制关闭失败: {e}")
            return False

    def check_and_kill_cursor(self):
        """检查Cursor是否运行，如果运行则关闭"""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'cursor.exe':
                    self.log_message("检测到Cursor正在运行，准备关闭...")
                    self.force_kill_cursor(show_confirm=False)
                    return True
            return False
        except Exception as e:
            self.log_message(f"检查Cursor进程失败: {e}")
            return False

    def start_cursor(self):
        """启动Cursor"""
        try:
            if sys.platform.startswith('win'):
                cursor_path = Path(os.getenv('LOCALAPPDATA')) / "Programs" / "Cursor" / "Cursor.exe"
                if cursor_path.exists():
                    subprocess.Popen([str(cursor_path)])
                    logger.info("已启动Cursor")
                    return True
            else:
                subprocess.Popen(['open', '-a', 'Cursor'])
                logger.info("已启动Cursor")
                return True
        except Exception as e:
            logger.error(f"启动Cursor失败: {e}")
            return False

    def load_current_ids(self):
        """读取当前ID"""
        try:
            if sys.platform.startswith('win'):
                storage_path = Path(os.getenv('APPDATA')) / "Cursor" / "User" / "globalStorage" / "storage.json"
            else:
                storage_path = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage" / "storage.json"
            
            if storage_path.exists():
                with open(storage_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.current_mac_id_label.setText(f"telemetry.macMachineId: {config.get('telemetry.macMachineId', '未找到')}")
                self.current_machine_id_label.setText(f"telemetry.machineId: {config.get('telemetry.machineId', '未找到')}")
                self.current_dev_id_label.setText(f"telemetry.devDeviceId: {config.get('telemetry.devDeviceId', '未找到')}")
                self.current_sqm_id_label.setText(f"telemetry.sqmId: {config.get('telemetry.sqmId', '未找到')}")
            else:
                self.log_message("未找到storage.json文件")
        except Exception as e:
            self.log_message(f"读取当前ID失败: {e}")

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        # 检查是否点击了标题栏区域
        if event.position().y() <= self.frameGeometry().height() - self.geometry().height():
            self._easter_egg_counter += 1
            self._easter_egg_timer.start(1000)  # 1秒内需要完成点击
            
            if self._easter_egg_counter >= 5:
                self._show_easter_egg()
                self._easter_egg_counter = 0
                self._easter_egg_timer.stop()
        
        # 添加点击粒子效果
        if event.button() == Qt.MouseButton.LeftButton:
            self.particle_effect.add_particles(event.position().x(), event.position().y())
        
        super().mousePressEvent(event)
    
    def _reset_easter_egg(self):
        """重置彩蛋计数器"""
        self._easter_egg_counter = 0
        self._easter_egg_timer.stop()

    def _show_easter_egg(self):
        """显示彩蛋动画"""
        # 清理现有动画
        if self._animation_group and self._animation_group.state() == QParallelAnimationGroup.State.Running:
            self._animation_group.stop()
            for label in self._easter_egg_labels:
                label.deleteLater()
            self._easter_egg_labels.clear()
            
        if self.heart_widget:
            self.heart_widget.deleteLater()
            
        # 创建新的动画组
        self._animation_group = QParallelAnimationGroup()
        
        # 创建全屏心形动画
        self.heart_widget = HeartAnimation()
        self.heart_widget.show()
        
        # 创建文本标签 - 确保显示在心形上方
        texts = [
            "安醇蛋蛋蛋",
            "爱",
            "霸王醇醇花"
        ]
        
        for i, text in enumerate(texts):
            label = QLabel(text)
            label.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
            label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Microsoft YaHei UI", 24, QFont.Weight.Bold))
            label.setStyleSheet("""
                QLabel {
                    color: #B76EFF;
                    padding: 10px;
                }
            """)
            
            # 设置标签大小和位置
            label.adjustSize()
            screen = QApplication.primaryScreen().geometry()
            label.move(
                (screen.width() - label.width()) // 2,
                -label.height()
            )
            
            # 创建动画
            anim = QPropertyAnimation(label, b"pos")
            anim.setDuration(1000)
            anim.setStartValue(QPoint(
                (screen.width() - label.width()) // 2,
                -label.height()
            ))
            anim.setEndValue(QPoint(
                (screen.width() - label.width()) // 2,
                screen.height() // 3 + i * 100
            ))
            anim.setEasingCurve(QEasingCurve.Type.OutBack)
            
            self._animation_group.addAnimation(anim)
            self._easter_egg_labels.append(label)
            label.show()
        
        # 启动动画
        self._animation_group.start()
        
        # 设置定时器在5秒后清除
        QTimer.singleShot(10000, self._clear_easter_egg)
        
    def _clear_easter_egg(self):
        """清除彩蛋动画"""
        if self._animation_group:
            self._animation_group.stop()
            for label in self._easter_egg_labels:
                label.deleteLater()
            self._easter_egg_labels.clear()
            self._animation_group = None
            
        if self.heart_widget:
            self.heart_widget.deleteLater()
            self.heart_widget = None

    def resizeEvent(self, event):
        """处理窗口大小改变"""
        super().resizeEvent(event)
        # 调整粒子效果层大小
        self.particle_effect.resize(self.size())
        
    def open_url(self, url):
        """打开URL链接"""
        import webbrowser
        webbrowser.open(url)

    def on_theme_changed(self, state):
        """主题切换处理"""
        if not self.follow_system.isChecked():
            self.update_theme(force_dark=bool(state))
            
    def on_follow_system_changed(self, state):
        """系统主题跟随切换处理"""
        self.theme_mode.setEnabled(not bool(state))
        if state:
            self.update_theme()  # 恢复跟随系统
            
    def update_theme(self, force_dark=None):
        """更新主题样式"""
        use_dark = force_dark if force_dark is not None else self.is_dark_mode()
        
        # 更新彩蛋提示颜色
        if use_dark:
            self.easter_hint.setStyleSheet("""
                QLabel {
                    color: #F2E6FF;
                    margin: 10px;
                }
            """)
        else:
            self.easter_hint.setStyleSheet("""
                QLabel {
                    color: #5D3F92;
                    margin: 10px;
                }
            """)
        
        if use_dark:
            # 深色主题样式
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2D1F3D;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #4A3A5A;
                    border-radius: 8px;
                    margin-top: 8px;
                    background-color: rgba(45, 31, 61, 0.7);
                    color: #E6CCFF;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0px 5px;
                    color: #B76EFF;
                }
                QPushButton {
                    background-color: #8A35D7;
                    color: white;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #9B4DE3;
                }
                QPushButton:pressed {
                    background-color: #7B1FA2;
                    padding-top: 9px;
                }
                QProgressBar {
                    border: 2px solid #4A3A5A;
                    border-radius: 6px;
                    text-align: center;
                    background-color: #2D1F3D;
                    color: #E6CCFF;
                }
                QProgressBar::chunk {
                    background-color: #B76EFF;
                    border-radius: 4px;
                }
                QLabel {
                    color: #E6CCFF;
                }
                QTextEdit {
                    border: 2px solid #4A3A5A;
                    border-radius: 6px;
                    background-color: rgba(45, 31, 61, 0.8);
                    color: #E6CCFF;
                }
                QTabWidget::pane {
                    border: 2px solid #4A3A5A;
                    border-radius: 6px;
                    background-color: rgba(45, 31, 61, 0.7);
                }
                QTabBar::tab {
                    background-color: #2D1F3D;
                    color: #E6CCFF;
                    border: 2px solid #4A3A5A;
                    border-bottom: none;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    padding: 5px 10px;
                }
                QTabBar::tab:selected {
                    background-color: #4A3A5A;
                    border-bottom: none;
                }
                QCheckBox {
                    color: #E6CCFF;
                }
                QCheckBox::indicator {
                    border: 2px solid #4A3A5A;
                    border-radius: 3px;
                    background-color: #2D1F3D;
                }
                QCheckBox::indicator:checked {
                    background-color: #B76EFF;
                }
                QPushButton#force_kill_button {
                    background-color: #FF4081;
                }
                QPushButton#force_kill_button:hover {
                    background-color: #F50057;
                }
                QPushButton#force_kill_button:pressed {
                    background-color: #C51162;
                }
                QLabel#copyright_label {
                    color: #B76EFF;
                    font-size: 12px;
                    padding: 10px;
                }
            """)
        else:
            # 浅色主题样式
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F2E6FF;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #E6CCFF;
                    border-radius: 8px;
                    margin-top: 8px;
                    background-color: rgba(255, 255, 255, 0.7);
                    color: #5D3F92;  /* 更柔和的紫色 */
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0px 5px;
                    color: #7E57C2;  /* 更柔和的紫色 */
                }
                QPushButton {
                    background-color: #9B4DE3;
                    color: white;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #8A35D7;
                }
                QPushButton:pressed {
                    background-color: #7B1FA2;
                    padding-top: 9px;
                }
                QProgressBar {
                    border: 2px solid #E6CCFF;
                    border-radius: 6px;
                    text-align: center;
                    background-color: white;
                    color: #5D3F92;  /* 更柔和的紫色 */
                }
                QProgressBar::chunk {
                    background-color: #9B4DE3;
                    border-radius: 4px;
                }
                QLabel {
                    color: #5D3F92;  /* 更柔和的紫色 */
                }
                QTextEdit {
                    border: 2px solid #E6CCFF;
                    border-radius: 6px;
                    background-color: rgba(255, 255, 255, 0.8);
                    color: #5D3F92;  /* 更柔和的紫色 */
                }
                QTabWidget::pane {
                    border: 2px solid #E6CCFF;
                    border-radius: 6px;
                    background-color: rgba(255, 255, 255, 0.7);
                }
                QTabBar::tab {
                    background-color: #F2E6FF;
                    color: #5D3F92;  /* 更柔和的紫色 */
                    border: 2px solid #E6CCFF;
                    border-bottom: none;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    padding: 5px 10px;
                }
                QTabBar::tab:selected {
                    background-color: #E6CCFF;
                    border-bottom: none;
                }
                QCheckBox {
                    color: #5D3F92;  /* 更柔和的紫色 */
                }
                QCheckBox::indicator {
                    border: 2px solid #E6CCFF;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #9B4DE3;
                }
                QPushButton#force_kill_button {
                    background-color: #FF4081;
                }
                QPushButton#force_kill_button:hover {
                    background-color: #F50057;
                }
                QPushButton#force_kill_button:pressed {
                    background-color: #C51162;
                }
                QLabel#copyright_label {
                    color: #7E57C2;  /* 更柔和的紫色 */
                    font-size: 12px;
                    padding: 10px;
                }
            """)
    
    def is_dark_mode(self):
        """检测系统是否为深色模式"""
        if sys.platform.startswith('win'):
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            except:
                return False
        elif sys.platform.startswith('darwin'):
            try:
                import subprocess
                cmd = 'defaults read -g AppleInterfaceStyle'
                subprocess.check_output(cmd.split())
                return True
            except:
                return False
        return False

    def register_cursor(self):
        """注册Cursor"""
        try:
            # 使用subprocess启动注册程序
            import subprocess
            import sys
            import os
            
            # 获取cursor_register.py的路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                base_path = sys._MEIPASS
            else:
                # 如果是直接运行的py文件
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            register_script = os.path.join(base_path, 'cursor_register.py')
            
            # 使用subprocess启动注册程序
            process = subprocess.Popen([sys.executable, register_script], 
                                     creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            self.log_message("启动注册程序成功")
            
        except Exception as e:
            self.log_message(f"启动注册程序失败: {e}")
            QMessageBox.critical(self, "错误", f"启动注册程序失败: {str(e)}")

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        import ctypes
        
        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception as e:
                logger.error(f"检查管理员权限失败: {e}")
                return False
        
        if not is_admin():
            try:
                # 使用绝对路径启动
                script_path = os.path.abspath(sys.argv[0])
                args = ' '.join(sys.argv[1:])
                
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas",
                    sys.executable,
                    f'"{script_path}" {args}',
                    None,
                    1
                )
                
                if ret <= 32:  # ShellExecute返回值小于32表示失败
                    raise RuntimeError(f"权限提升失败,错误码:{ret}")
                    
                sys.exit(0)  # 正常退出
                
            except Exception as e:
                logger.error(f"请求管理员权限失败: {e}")
                QMessageBox.critical(None, "错误", 
                    "需要管理员权限才能运行此程序。\n"
                    f"错误详情: {str(e)}")
                sys.exit(1)
    
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        QMessageBox.critical(None, "错误", 
            f"程序运行出错: {str(e)}")
        sys.exit(1)