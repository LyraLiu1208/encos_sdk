"""
数据类型定义模块
================

定义SDK中使用的各种数据结构、枚举类型和常量。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import struct


class FeedbackType(Enum):
    """反馈报文类型"""
    TYPE_1 = 1  # 位置、速度、力矩反馈
    TYPE_2 = 2  # 位置、速度、电流反馈  
    TYPE_3 = 3  # 位置、速度反馈
    TYPE_4 = 4  # 电机状态反馈
    TYPE_5 = 5  # 电机错误反馈


class ErrorCode(Enum):
    """错误代码枚举"""
    NO_ERROR = 0x00
    OVER_VOLTAGE = 0x01      # 过压
    UNDER_VOLTAGE = 0x02     # 欠压
    OVER_CURRENT = 0x04      # 过流
    OVER_TEMPERATURE = 0x08  # 过温
    ENCODER_ERROR = 0x10     # 编码器错误
    HALL_ERROR = 0x20        # 霍尔传感器错误
    UNKNOWN_ERROR = 0xFF     # 未知错误


class MotorMode(Enum):
    """电机控制模式"""
    FORCE_POSITION = 1   # 力位混控模式
    SERVO_POSITION = 2   # 伺服位置模式  
    SERVO_SPEED = 3      # 伺服速度模式
    CURRENT_CONTROL = 4  # 电流控制模式


@dataclass
class MotorStatus:
    """电机状态数据结构"""
    motor_id: int
    position: float = 0.0        # 位置 (度)
    velocity: float = 0.0        # 速度 (RPM)
    current: float = 0.0         # 电流 (A)
    torque: float = 0.0          # 力矩 (N·m)
    temperature: float = 0.0     # 温度 (°C)
    error_code: ErrorCode = ErrorCode.NO_ERROR
    voltage: float = 0.0         # 电压 (V)
    feedback_type: Optional[FeedbackType] = None
    
    def has_error(self) -> bool:
        """检查是否有错误"""
        return self.error_code != ErrorCode.NO_ERROR
    
    def get_error_description(self) -> str:
        """获取错误描述"""
        error_descriptions = {
            ErrorCode.NO_ERROR: "无错误",
            ErrorCode.OVER_VOLTAGE: "过压保护",
            ErrorCode.UNDER_VOLTAGE: "欠压保护", 
            ErrorCode.OVER_CURRENT: "过流保护",
            ErrorCode.OVER_TEMPERATURE: "过温保护",
            ErrorCode.ENCODER_ERROR: "编码器错误",
            ErrorCode.HALL_ERROR: "霍尔传感器错误",
            ErrorCode.UNKNOWN_ERROR: "未知错误"
        }
        return error_descriptions.get(self.error_code, "未定义错误")


@dataclass
class CANFrame:
    """CAN数据帧结构"""
    arbitration_id: int      # CAN ID
    data: bytes             # 数据负载 (最多8字节)
    is_extended: bool = False
    
    def __post_init__(self):
        if len(self.data) > 8:
            raise ValueError("CAN数据负载不能超过8字节")


# CAN协议常量
class ProtocolConstants:
    """协议常量定义"""
    
    # CAN波特率
    CAN_BITRATE = 1000000  # 1Mbps
    
    # 心跳保护时间
    HEARTBEAT_TIMEOUT_MS = 500
    
    # 指令间隔时间
    COMMAND_INTERVAL_MS = 500
    
    # 默认CAN ID范围
    DEFAULT_MOTOR_ID_MIN = 1
    DEFAULT_MOTOR_ID_MAX = 32
    
    # 数据转换常量
    POSITION_SCALE = 6.28318 / 65536  # 位置换算: 弧度/LSB
    VELOCITY_SCALE = 0.1             # 速度换算: RPM/LSB  
    CURRENT_SCALE = 0.01             # 电流换算: A/LSB
    TORQUE_SCALE = 0.01              # 力矩换算: N·m/LSB
    TEMPERATURE_SCALE = 0.1          # 温度换算: °C/LSB
    
    # 控制参数范围
    KP_MAX = 4095
    KD_MAX = 511
    POSITION_MAX = 65535
    VELOCITY_MAX = 2047
    TORQUE_MAX = 2047


def float_to_bytes(value: float) -> bytes:
    """将float32转换为4字节数组 (大端序)"""
    return struct.pack('>f', value)


def bytes_to_float(data: bytes) -> float:
    """将4字节数组转换为float32 (大端序)"""
    return struct.unpack('>f', data)[0]


def scale_to_range(value: float, min_val: float, max_val: float, bit_range: int) -> int:
    """将物理值缩放到指定位数范围"""
    if value < min_val:
        value = min_val
    elif value > max_val:
        value = max_val
    
    ratio = (value - min_val) / (max_val - min_val)
    return int(ratio * ((1 << bit_range) - 1))


def unscale_from_range(scaled_value: int, min_val: float, max_val: float, bit_range: int) -> float:
    """将位数范围值还原为物理值"""
    ratio = scaled_value / ((1 << bit_range) - 1)
    return min_val + ratio * (max_val - min_val)
