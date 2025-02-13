# 更新了自动注册
![7b5f0b31f447ee3189061044065276d7](https://github.com/user-attachments/assets/70ad7478-01da-4136-897c-d5db0aa53c0e)
可以点击注册cursor进行自动注册
但是一定记得要填写验证码
![e53e1834074bef7cf8b4c486641ff437](https://github.com/user-attachments/assets/004c7bf9-8272-4122-a29a-fb66e2e19e9d)

自动注册打磨的还是不够好
后续想办法接入我自己的部署的虚拟邮箱
## 🙏 特别鸣谢 | Special Thanks

本项目的开发过程中得到了众多开源项目和社区成员的支持与帮助,在此特别感谢:

### 开源项目

- [hamflx/cursor-reset](https://github.com/hamflx/cursor-reset) - 提供了初始的技术思路和实现方案
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 优秀的GUI框架支持
- [psutil](https://github.com/giampaolo/psutil) - 提供了可靠的进程管理功能
- [cursor-free-vip](https://github.com/yeongpin/cursor-free-vip/tree/main)- 提供自动注册

### 技术支持

感谢以下项目和文档对本项目的技术支持:

- Windows Registry Documentation - 提供了注册表操作的技术规范
- UUID RFC 4122 - 为设备ID生成提供了标准规范
- Python Software Foundation - 提供了强大的Python运行时支持

### 社区贡献

感谢所有为本项目提供反馈、建议和代码贡献的社区成员。您的支持是本项目不断改进的动力。

# Cursor ID 0.45.x 重置工具开源声明

## ⚠️ 免责声明 | Disclaimer

**本项目仅用于学术研究目的**，旨在研究现代 IDE 软件的设备标识机制。我们强烈建议通过官方渠道获取 Cursor 的正版授权。

**重要提醒**：使用者需自行承担以下风险：

- 软件授权失效风险
- 账号封禁风险
- 注册表修改导致的系统不稳定

**This is an academic research project** studying device identification mechanisms in modern IDEs. We strongly recommend obtaining official Cursor licenses through proper channels.

**Critical Notice**: Users assume all risks including but not limited to:

- License invalidation
- Account suspension
- System instability from registry modifications

---

## 📝 项目背景 | Background

本项目提供 Windows 系统下 Cursor IDE 0.45.x 系列（0.45.8 已验证）的设备标识重置解决方案。该项目采用 PyQt6 构建 GUI 界面，通过修改注册表机制和配置文件实现设备指纹重置。

![GUI 界面](https://github.com/user-attachments/assets/0fc581b5-088d-493d-91bf-12268e2eb87a)

---

## 🛠️ 下载链接

最新版也可以重置

[下载链接]
https://ajq.lanzouv.com/iCERC2mu0gfg
密码: `4cbc`

### 无广告代码已经更新

![无广告代码更新](https://github.com/user-attachments/assets/17745383-c21d-4bbd-9755-8d9bdae0104a)

---

## 🛠️ 技术特性 | Technical Features

```python
class IDGenerator:
    # 生成符合Cursor规范的设备ID
    @staticmethod
    def generate_mac_machine_id():
        """生成符合v4规范的UUID"""
        template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
        return uuid.uuid4().hex
```

| 功能模块          | 实现原理                     |
|-------------------|----------------------------|
| 设备 ID 生成器      | 基于 RFC4122 规范实现 v4 UUID  |
| 注册表操作        | 通过 winreg 模块修改 MachineGuid |
| 进程管理          | 使用 psutil 进行进程监控       |

---

## 📥 安装与使用 | Installation & Usage

### 系统要求 | Requirements

- Windows 10/11 64 位
- Python 3.8+
- 管理员权限运行

### 图形界面操作流程

1.  关闭 Cursor IDE 进程
2.  执行 `main.py` 启动重置工具
3.  点击 "开始重置" 按钮
4.  按照提示完成操作

---

## 🔧 技术架构 | Architecture

```mermaid
graph TD
    A[GUI界面] --> B[进程检测模块]
    B --> C[注册表备份模块]
    C --> D[ID生成引擎]
    D --> E[注册表写入模块]
    E --> F[配置文件更新]
```

---

## 🙏 鸣谢 | Acknowledgments

特别感谢 [hamflx/cursor-reset](https://github.com/hamflx/cursor-reset) 项目提供的初始研究思路，本工具在其基础之上进行了以下增强：

-   增加了 GUI 可视化界面
-   完善了注册表备份/恢复机制
-   添加了进程状态实时监控功能

---

## 📄 许可协议 | License

本项目采用 GPLv3 协议发布，商业使用需经作者书面授权
本项目使用 MIT 开源许可，详情请参考 `LICENSE` 文件。
```text
© 2024 ayc404. All rights reserved.
未经明确书面授权，任何企业/个人不得将本项目用于商业用途。
```

---

## 💬 反馈渠道 | Support

遇到技术问题请提交 issue，或通过以下方式联系我们：

-   电子邮箱：anjiaqi404@qq.com

---

> 附：本工具包含 Easter Egg 彩蛋功能，连续点击标题栏五次即可触发特殊动画效果 🎉

### 项目简介

本工具旨在解决 Cursor IDE 的设备 ID 重置问题，支持 Cursor 0.45.x 版本（已在 0.45.8 版本上测试通过）。

### ⚠️  免责声明

-   本项目仅供学习和研究，旨在研究 Cursor IDE 的设备识别机制。
-   **强烈建议您购买 Cursor 的正版授权**，以支持开发者。
-   使用本工具可能违反 Cursor 的使用条款。作者不对使用本工具导致的任何问题负责，包括但不限于：
    -   软件授权失效
    -   账号封禁
    -   其他未知风险
-   如果您认可 Cursor 的价值，请支持正版，为软件开发者的工作付费。

### 主要功能

本工具的主要功能如下：

-   **ID 重置**：生成新的设备 ID，并修改 Cursor 的配置文件和系统注册表（仅 Windows 系统）。
-   **ID 备份**：备份当前的设备 ID，以便在需要时恢复。
-   **强制关闭**：提供强制关闭 Cursor IDE 的功能，避免重置过程中出现问题。
-   **日志记录**：详细记录重置过程中的操作，方便用户查看。
-   **彩蛋功能**：有趣的彩蛋，可通过点击标题栏触发。

###  🛠️ 使用方法

#### 1. Windows 系统

-   在 Cursor IDE 中退出当前登录的账号。
-   完全关闭 Cursor IDE。
-   以管理员身份运行本工具。
-   点击“开始重置”按钮，按照提示操作。
-   重置完成后，打开 Cursor IDE 并使用新账号登录（**不要使用之前的账号**）。

#### 2. macOS 系统

-   由于本项目暂无 macOS 版本，请参考 [hamflx/cursor-reset](https://github.com/hamflx/cursor-reset) 项目中的说明进行操作。
-   或者考虑使用我提供的 Windows 版本（如果方便的话）。

### ⚠️  重要注意事项

#### 1. Windows 系统

-   本工具会修改系统注册表中的 `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid`，该值可能被其他软件用作设备标识。如果修改后其他软件的授权失效，请自行承担后果。
-   原始的 `MachineGuid` 会被自动备份到 `%USERPROFILE%\CursorReset_Backups` 目录下。
-   如果需要恢复原始 `MachineGuid`，请从备份目录中找到对应的备份文件，然后使用注册表编辑器恢复该值。

#### 2. macOS 系统

-   本项目暂无 macOS 系统支持。
-   请参考 `hamflx/cursor-reset` 项目，使用其脚本。
-   其脚本会创建一个假的 `ioreg` 命令来模拟不同的设备标识。
-   原始的 `IOPlatformUUID` 会被备份到 `~/CursorReset_Backups` 目录下。
-    这个方法不会永久修改系统设置，但需要保持 PATH 环境变量的修改才能持续生效。


### 系统要求

#### 1. Windows 系统

-   Windows 操作系统
-   管理员权限
-   Cursor IDE 0.45.x 版本（已在 0.45.8 版本测试通过）

### 开源许可

本项目使用 MIT 开源许可，详情请参考 `LICENSE` 文件。

### 感谢

-   感谢 [hamflx/cursor-reset](https://github.com/hamflx/cursor-reset) 项目提供的思路和代码参考。

### 作者

-   ayc404
---

# Cursor Identity Reset Utility (光标设备标识重置工具)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-GPLv3-orange.svg)

## 📝 项目背景 | Background

本项目提供 Windows 系统下 Cursor IDE 0.45.x 系列（0.45.8 已验证）的设备标识重置解决方案。该项目采用 PyQt6 构建 GUI 界面，通过修改注册表机制和配置文件实现设备指纹重置。

![GUI 界面](https://github.com/user-attachments/assets/0fc581b5-088d-493d-91bf-12268e2eb87a)

This project provides a device identity reset solution for Cursor IDE 0.45.x series (verified on 0.45.8) on Windows systems. Built with PyQt6 GUI framework, it modifies both registry entries and configuration files to reset device fingerprints.

# 赞赏码请我喝杯蜜雪

![Collage_20250114_125849](https://github.com/user-attachments/assets/fbffa538-306b-4902-9a21-46b433c28e26)


# SiliconCloud 裂变活动火热开启！2000 万 Tokens 等你来领！

大家好！今天我们为大家带来一个超值的活动——**SiliconCloud 裂变活动**，2000 万 Tokens 等你来领！

## 活动详情

**北京时间 2024 年 8 月 1 日起**，每成功邀请一位新用户注册 SiliconCloud，您和好友均可获得 **2000 万 Tokens**（价值 14 元平台配额）。邀请越多，奖励越多，快来体验 SiliconCloud 的强大功能！

### 活动规则

1.  **邀请好友赚 Tokens**：每成功邀请一位新用户，您将获得 2000 万 Tokens。
2.  **注册即送 Tokens**：受邀好友完成注册后，立即获得 2000 万 Tokens。
3.  **14 元配额**：新用户还可获得 14 元平台配额，体验流畅的 DeepSeek API，告别卡顿网络版本！

## 立即注册

**点击下方链接，注册 SiliconCloud**

或复制链接到浏览器注册：[https://cloud.siliconflow.cn/i/CoW8MS0u](https://cloud.siliconflow.cn/i/CoW8MS0u)

**快来参与裂变活动，邀请好友一起体验 SiliconCloud 的强大功能吧！**

# 帮我助力一下谢谢各位
# Help me, thank you everyone
