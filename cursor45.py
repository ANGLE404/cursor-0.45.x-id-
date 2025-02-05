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
        self.size = random.randint(1, 3)
        self.life = 1.0
        self.color = QColor("#F2E6FF")
        
        # 修改力的计算方式，避免除零错误
        dx = x - self.x
        dy = y - self.y
        distance = max(0.1, (dx * dx + dy * dy) ** 0.6)  # 添加最小值避免除零
        force = -1 / distance
        
        self.vx = random.uniform(-2, 2) * force
        self.vy = random.uniform(-2, 2) * force

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.02
        alpha = max(0.0, min(1.0, self.life))  # 确保alpha在0到1之间
        self.color.setAlphaF(alpha)
        return self.life > 0

def heart_function(t, shrink_ratio=11):
    """爱心函数生成器"""
    x = 16 * (sin(t) ** 3)
    y = -(13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t))
    
    # 放大
    x *= shrink_ratio
    y *= shrink_ratio
    
    return x, y

class HeartShape(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = set()
        self.edge_particles = set()
        self.center_particles = set()
        self.halo_particles = set()
        
        # 调整基础参数，增大中心点坐标使爱心完整显示
        self.canvas_center_x = 200  # 增大中心X坐标
        self.canvas_center_y = 200  # 增大中心Y坐标
        self.image_enlarge = 11
        
        # 设置widget背景为黑色
        self.setStyleSheet("background-color: black;")
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(33)  # ~30fps
        
        self.frame = 0
        # 等待一小段时间再初始化粒子，确保窗口尺寸已经设置好
        QTimer.singleShot(100, lambda: self.build(2000))
    
    def scatter_inside(self, x, y, beta=0.15):
        """散射函数"""
        ratiox = -beta * log(random.random())
        ratioy = -beta * log(random.random())
        dx = ratiox * (x - self.canvas_center_x)
        dy = ratioy * (y - self.canvas_center_y)
        return x - dx, y - dy
    
    def heart_function(self, t, shrink_ratio=11):
        """爱心函数"""
        x = 16 * (sin(t) ** 3)
        y = -(13 * cos(t) - 5 * cos(2*t) - 2 * cos(3*t) - cos(4*t))
        
        x *= shrink_ratio
        y *= shrink_ratio
        
        x += self.canvas_center_x
        y += self.canvas_center_y
        
        return x, y
    
    def shrink(self, x, y, ratio):
        """收缩效果"""
        sk_range = -1 / (((x-self.canvas_center_x) ** 2 + (y-self.canvas_center_y) ** 2) + 1)
        dx = ratio * sk_range * (x-self.canvas_center_x)
        dy = ratio * sk_range * (y-self.canvas_center_y)
        return x - dx, y - dy
    
    def build(self, number):
        """构建初始粒子"""
        # 基础爱心轮廓
        for _ in range(number):
            t = random.uniform(0, 2 * pi)
            x, y = self.heart_function(t)
            x, y = self.shrink(x, y, -1000)
            self.particles.add((x, y))
        
        # 边缘扩散
        for px, py in self.particles:
            for _ in range(3):
                x, y = self.scatter_inside(px, py, 0.05)
                self.edge_particles.add((x, y))
        
        # 中心扩散
        particle_list = list(self.particles)
        for _ in range(4000):
            x, y = random.choice(particle_list)
            x, y = self.scatter_inside(x, y)
            self.center_particles.add((x, y))
    
    def cal_position(self, x, y, ratio):
        """计算心跳位置"""
        bt_range = 1 / (((x-self.canvas_center_x) ** 2 + (y-self.canvas_center_y) ** 2) + 1)
        dx = ratio * bt_range * (x-self.canvas_center_x)
        dy = ratio * bt_range * (y-self.canvas_center_y)
        return x - dx, y - dy
    
    def update_particles(self):
        """更新粒子状态"""
        self.frame += 1
        ratio = 1000 + 150 * sin(self.frame / 10 * pi)
        
        # 更新光晕
        self.halo_particles.clear()
        halo_radius = int(4 + 3 * (1 + sin(self.frame / 30 * pi)))
        halo_number = int(4000 + 2000 * abs(sin(self.frame / 30 * pi)))
        
        for _ in range(halo_number):
            t = random.uniform(0, 2 * pi)
            x, y = self.heart_function(t, 11.6)
            x, y = self.shrink(x, y, halo_radius)
            x += random.uniform(-8, 8)
            y += random.uniform(-8, 8)
            self.halo_particles.add((x, y))
        
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算心跳颜色
        pulse = sin(self.frame / 10 * pi)
        r = max(0, min(255, 155 + int(20 * pulse)))
        g = max(0, min(255, 77 + int(20 * pulse)))
        b = max(0, min(255, 227 + int(20 * pulse)))
        color = QColor(r, g, b)
        
        # 绘制所有粒子
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        
        ratio = 1000 + 150 * sin(self.frame / 10 * pi)
        
        # 绘制光晕粒子
        for x, y in self.halo_particles:
            size = random.uniform(1, 2)
            painter.drawEllipse(QPointF(x, y), size, size)
        
        # 绘制主体轮廓
        for x, y in self.particles:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(2, 3)
            painter.drawEllipse(QPointF(x, y), size, size)
        
        # 绘制边缘粒子
        for x, y in self.edge_particles:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(1.5, 2.5)
            painter.drawEllipse(QPointF(x, y), size, size)
        
        # 绘制中心粒子
        for x, y in self.center_particles:
            x, y = self.cal_position(x, y, ratio)
            size = random.uniform(1, 2)
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cursor ID 重置工具")
        self.setMinimumSize(500, 400)
        
        # 初始化彩蛋相关变量
        self._easter_egg_counter = 0
        self._easter_egg_labels = []
        self._animation_group = None
        self._easter_egg_texts = [
            "安醇蛋蛋蛋",
            "爱",
            "霸王醇醇花"
        ]
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建主窗口部件
        main_widget = QWidget()
        layout.addWidget(main_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 创建选项卡
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # 主要操作选项卡
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
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("开始重置")
        self.reset_button.clicked.connect(self.start_reset)
        button_layout.addWidget(self.reset_button)
        
        self.backup_button = QPushButton("备份当前ID")
        self.backup_button.clicked.connect(self.backup_ids)
        button_layout.addWidget(self.backup_button)
        
        self.force_kill_button = QPushButton("强制关闭Cursor")
        self.force_kill_button.clicked.connect(self.force_kill_cursor)
        self.force_kill_button.setObjectName("force_kill_button")
        button_layout.addWidget(self.force_kill_button)
        
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
        
        # 在设置标签页添加彩蛋提示和按钮
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # 添加彩蛋提示
        easter_hint = QLabel("💗 小彩蛋：连续点击5次标题栏试试看~ 💗")
        easter_hint.setStyleSheet("""
            QLabel {
                color: #F2E6FF;
                font-size: 12px;
                margin: 10px;
            }
        """)
        settings_layout.addWidget(easter_hint)
        
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
        
        tabs.addTab(settings_tab, "设置")
        
        # 添加底部版权信息
        copyright_label = QLabel("© ayc404制作 拒绝商用")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setObjectName("copyright_label")
        layout.addWidget(copyright_label)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                width: 10px;
                margin: 0.5px;
            }
            QPushButton#force_kill_button {
                background-color: #d93025;
            }
            QPushButton#force_kill_button:hover {
                background-color: #b3261e;
            }
            QPushButton#force_kill_button:pressed {
                background-color: #8c1d18;
            }
            QLabel#copyright_label {
                color: #666666;
                font-size: 12px;
                padding: 10px;
            }
        """)
        
        # 初始化工作线程
        self.worker = None
        
        # 读取当前ID
        self.load_current_ids()
    
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
        """鼠标点击事件处理"""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                # 检查是否点击在标题位置
                if 0 <= event.position().y() <= 30:
                    self._easter_egg_counter += 1
                    if self._easter_egg_counter >= 5:  # 连续点击5次触发
                        self._show_easter_egg()
                        self._easter_egg_counter = 0  # 重置计数器
        except Exception as e:
            logger.error(f"彩蛋触发失败: {e}")
        super().mousePressEvent(event)
    
    def _show_easter_egg(self):
        """显示彩蛋动画"""
        # 清理旧的动画
        if self._animation_group:
            self._animation_group.stop()
        for label in self._easter_egg_labels:
            label.deleteLater()
        self._easter_egg_labels.clear()
        
        # 创建爱心形状，增大尺寸
        heart = HeartShape(self)
        heart.resize(400, 400)  # 增大尺寸
        heart.move((self.width() - heart.width())//2, 
                   (self.height() - heart.height())//2 - 100)
        heart.show()
        self._easter_egg_labels.append(heart)
        
        # 创建文字标签
        for i, text in enumerate(self._easter_egg_texts):
            label = QLabel(text, self)
            label.setStyleSheet("""
                QLabel {
                    color: #F2E6FF;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.resize(400, 50)
            # 调整文字位置，放在爱心下方
            label.move(
                (self.width() - label.width()) // 2,
                (self.height() + heart.height()) // 2 - 50 + i * 60
            )
            label.show()
            self._easter_egg_labels.append(label)
        
        # 将显示时间延长到30秒
        QTimer.singleShot(30000, self._hide_easter_egg)
    
    def _hide_easter_egg(self):
        """隐藏彩蛋"""
        for label in self._easter_egg_labels:
            label.deleteLater()
        self._easter_egg_labels.clear()
        self._easter_egg_counter = 0
    
    def resizeEvent(self, event):
        """窗口大小改变时重新定位标签"""
        super().resizeEvent(event)
        if self._easter_egg_labels:
            for i, label in enumerate(self._easter_egg_labels):
                label.move(
                    (self.width() - label.width()) // 2,
                    (self.height() - len(self._easter_egg_labels) * 60) // 2 + i * 60
                )

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        import ctypes
        
        # 检查是否具有管理员权限
        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        
        # 如果没有管理员权限，则请求提升
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())