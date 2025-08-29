"""
电机控制SDK
=============

这是一个完整的电机控制软件开发工具包(SDK)，基于CAN总线通信协议。
SDK采用四层架构设计，提供从底层硬件通信到高级应用接口的完整解决方案。

架构层次：
1. 硬件通信层 (hardware_layer.py) - CAN总线硬件接口
2. 协议编码/解码层 (protocol_layer.py) - CAN报文格式处理
3. 电机控制API层 (motor_api.py) - 高级电机控制接口
4. 用户交互层 (cli_tool.py) - 命令行工具

安装要求：
- Python 3.7+
- python-can库
- USB-CAN分析仪硬件

快速开始：
```python
from encos_sdk import Motor, CANHardware

# 初始化硬件
can_hw = CANHardware(interface='socketcan', channel='can0', bitrate=1000000)

# 创建电机实例
motor = Motor(motor_id=1, can_hardware=can_hw)

# 基本操作
motor.set_zero_point()          # 设置零点
motor.set_position(90.0)        # 设置位置到90度
status = motor.get_status()     # 获取状态反馈
```

CLI工具使用：
```bash
python cli_tool.py scan                    # 扫描总线上的电机
python cli_tool.py zero 1                  # 设置电机1的零点
python cli_tool.py pos 1 90 100 5.0       # 电机1位置控制
python cli_tool.py monitor 1              # 监控电机1状态
```

安全注意事项：
- 测试前务必固定电机
- 避免在未固定情况下测试电流/力矩模式
- 注意500ms心跳保护机制
- 设置类指令间隔至少500ms

更多详细信息请参考各模块的文档说明。
"""

__version__ = "1.0.0"
__author__ = "Dyna Team"

# 导入主要类和函数，方便外部使用
from .hardware_layer import CANHardware
from .motor_api import Motor, MotorManager
from .protocol_layer import ProtocolEncoder, ProtocolDecoder
from .data_types import MotorStatus, ErrorCode, FeedbackType

__all__ = [
    'CANHardware',
    'Motor',
    'MotorManager',
    'ProtocolEncoder',
    'ProtocolDecoder',
    'MotorStatus',
    'ErrorCode',
    'FeedbackType'
]
