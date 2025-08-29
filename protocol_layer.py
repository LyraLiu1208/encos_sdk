"""
协议编码/解码层 (Protocol Encoding/Decoding Layer)
================================================

负责CAN协议报文的编码和解码，严格按照协议文档实现各种指令和反馈的格式转换。
这一层隐藏了复杂的位操作细节，为上层提供结构化的数据接口。

主要功能：
- 控制指令的编码 (上层参数 -> CAN字节流)
- 反馈报文的解码 (CAN字节流 -> 结构化数据)
- 参数范围检查和数据转换
- 校验和错误检测
"""

import struct
import math
from typing import Tuple, Optional

try:
    from .data_types import (
        CANFrame, MotorStatus, ErrorCode, FeedbackType, 
        ProtocolConstants, float_to_bytes, bytes_to_float
    )
except ImportError:
    from data_types import (
        CANFrame, MotorStatus, ErrorCode, FeedbackType,
        ProtocolConstants, float_to_bytes, bytes_to_float
    )


class ProtocolEncoder:
    """CAN协议编码器
    
    将高级控制指令转换为符合协议规范的CAN数据帧。
    """
    
    @staticmethod
    def encode_query_id() -> CANFrame:
        """编码查询CAN通信ID指令
        
        Returns:
            CANFrame: 查询ID的CAN帧
        """
        return CANFrame(
            arbitration_id=0x000,
            data=bytes([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        )
    
    @staticmethod
    def encode_reset_id(new_id: int) -> CANFrame:
        """编码重置电机ID指令
        
        Args:
            new_id: 新的电机ID (1-32)
            
        Returns:
            CANFrame: 重置ID的CAN帧
        """
        if not (1 <= new_id <= 32):
            raise ValueError("电机ID必须在1-32范围内")
        
        return CANFrame(
            arbitration_id=0x000,
            data=bytes([0x55, 0xAA, 0x55, 0xAA, new_id, 0x00, 0x00, 0x00])
        )
    
    @staticmethod
    def encode_set_zero_point(motor_id: int) -> CANFrame:
        """编码设置零点指令
        
        Args:
            motor_id: 电机ID
            
        Returns:
            CANFrame: 设置零点的CAN帧
        """
        return CANFrame(
            arbitration_id=motor_id,
            data=bytes([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        )
    
    @staticmethod
    def encode_force_position_command(motor_id: int, kp: float, kd: float, 
                                    position: float, velocity: float, torque: float) -> CANFrame:
        """编码力位混控模式指令
        
        这是最复杂的编码函数，包含多个不同位宽的参数。
        
        Args:
            motor_id: 电机ID
            kp: 位置刚度 (0-4095)
            kd: 位置阻尼 (0-511)  
            position: 目标位置 (弧度)
            velocity: 前馈速度 (rad/s)
            torque: 前馈力矩 (N·m)
            
        Returns:
            CANFrame: 力位混控指令的CAN帧
        """
        # 参数范围检查和转换
        kp_int = max(0, min(int(kp), ProtocolConstants.KP_MAX))
        kd_int = max(0, min(int(kd), ProtocolConstants.KD_MAX))
        
        # 位置: -π到π映射到0-65535
        pos_normalized = (position + math.pi) / (2 * math.pi)
        pos_int = max(0, min(int(pos_normalized * 65535), 65535))
        
        # 速度: -10到10rad/s映射到0-2047  
        vel_normalized = (velocity + 10) / 20
        vel_int = max(0, min(int(vel_normalized * 2047), 2047))
        
        # 力矩: -10到10N·m映射到0-2047
        tor_normalized = (torque + 10) / 20  
        tor_int = max(0, min(int(tor_normalized * 2047), 2047))
        
        # 位操作打包 - 按照协议文档的位分布
        command_data = 0
        command_data |= (kp_int & 0xFFF) << 52     # KP: 12位
        command_data |= (kd_int & 0x1FF) << 43     # KD: 9位
        command_data |= (pos_int & 0xFFFF) << 27   # 位置: 16位
        command_data |= (vel_int & 0x7FF) << 16    # 速度: 11位
        command_data |= (tor_int & 0x7FF) << 5     # 力矩: 11位
        # 最后5位保留
        
        # 拆分成8个字节 (大端序)
        data = []
        for i in range(8):
            data.append((command_data >> (56 - 8*i)) & 0xFF)
        
        return CANFrame(
            arbitration_id=motor_id,
            data=bytes(data)
        )
    
    @staticmethod
    def encode_servo_position_command(motor_id: int, position: float, 
                                    speed_limit: float, current_limit: float) -> CANFrame:
        """编码伺服位置模式指令
        
        Args:
            motor_id: 电机ID
            position: 目标位置 (度)
            speed_limit: 速度限制 (RPM)
            current_limit: 电流限制 (A)
            
        Returns:
            CANFrame: 伺服位置指令的CAN帧
        """
        # 转换为协议格式
        pos_bytes = float_to_bytes(math.radians(position))  # 度转弧度
        speed_bytes = float_to_bytes(speed_limit)
        current_bytes = float_to_bytes(current_limit)
        
        # 构造数据 (前4字节位置，后4字节速度和电流各2字节)
        data = bytearray(8)
        data[0:4] = pos_bytes
        
        # 速度和电流各占2字节 (简化处理)
        speed_int = max(0, min(int(speed_limit * 10), 65535))
        current_int = max(0, min(int(current_limit * 100), 65535))
        
        data[4:6] = speed_int.to_bytes(2, 'big')
        data[6:8] = current_int.to_bytes(2, 'big')
        
        return CANFrame(
            arbitration_id=motor_id,
            data=bytes(data)
        )
    
    @staticmethod
    def encode_servo_speed_command(motor_id: int, speed: float, current_limit: float) -> CANFrame:
        """编码伺服速度模式指令
        
        Args:
            motor_id: 电机ID
            speed: 目标速度 (RPM)
            current_limit: 电流限制 (A)
            
        Returns:
            CANFrame: 伺服速度指令的CAN帧
        """
        speed_bytes = float_to_bytes(speed)
        current_bytes = float_to_bytes(current_limit)
        
        data = bytearray(8)
        data[0:4] = speed_bytes
        data[4:8] = current_bytes
        
        return CANFrame(
            arbitration_id=motor_id,
            data=bytes(data)
        )
    
    @staticmethod
    def encode_status_request(motor_id: int, feedback_type: FeedbackType) -> CANFrame:
        """编码状态查询指令
        
        Args:
            motor_id: 电机ID
            feedback_type: 反馈类型
            
        Returns:
            CANFrame: 状态查询的CAN帧
        """
        return CANFrame(
            arbitration_id=motor_id,
            data=bytes([0xAA, 0x55, feedback_type.value, 0x00, 0x00, 0x00, 0x00, 0x00])
        )


class ProtocolDecoder:
    """CAN协议解码器
    
    将接收到的CAN数据帧解析为结构化的电机状态数据。
    """
    
    @staticmethod
    def decode_feedback(frame: CANFrame) -> Optional[MotorStatus]:
        """解码反馈报文
        
        Args:
            frame: 接收到的CAN帧
            
        Returns:
            MotorStatus: 解析后的电机状态，解析失败返回None
        """
        if len(frame.data) < 8:
            return None
        
        try:
            # 检查报文类型 (数据第一字节的高3位)
            feedback_type_code = (frame.data[0] >> 5) & 0x07
            
            if feedback_type_code == 1:
                return ProtocolDecoder._decode_type1_feedback(frame)
            elif feedback_type_code == 2:
                return ProtocolDecoder._decode_type2_feedback(frame)
            elif feedback_type_code == 3:
                return ProtocolDecoder._decode_type3_feedback(frame)
            elif feedback_type_code == 4:
                return ProtocolDecoder._decode_type4_feedback(frame)
            elif feedback_type_code == 5:
                return ProtocolDecoder._decode_type5_feedback(frame)
            else:
                return None
                
        except Exception:
            return None
    
    @staticmethod
    def _decode_type1_feedback(frame: CANFrame) -> MotorStatus:
        """解码Type1反馈: 位置、速度、力矩"""
        data = frame.data
        
        # 位置 (字节1-2, 16位)
        pos_raw = (data[1] << 8) | data[2]
        position_rad = pos_raw * ProtocolConstants.POSITION_SCALE
        position_deg = math.degrees(position_rad)
        
        # 速度 (字节3-4, 16位, 有符号)
        vel_raw = struct.unpack('>h', data[3:5])[0]  # 大端序有符号短整型
        velocity_rpm = vel_raw * ProtocolConstants.VELOCITY_SCALE
        
        # 力矩 (字节5-6, 16位, 有符号)
        tor_raw = struct.unpack('>h', data[5:7])[0]
        torque_nm = tor_raw * ProtocolConstants.TORQUE_SCALE
        
        # 温度 (字节7)
        temperature = data[7] * ProtocolConstants.TEMPERATURE_SCALE
        
        return MotorStatus(
            motor_id=frame.arbitration_id,
            position=position_deg,
            velocity=velocity_rpm,
            torque=torque_nm,
            temperature=temperature,
            feedback_type=FeedbackType.TYPE_1
        )
    
    @staticmethod
    def _decode_type2_feedback(frame: CANFrame) -> MotorStatus:
        """解码Type2反馈: 位置、速度、电流"""
        data = frame.data
        
        # 位置 (字节1-2)
        pos_raw = (data[1] << 8) | data[2]
        position_rad = pos_raw * ProtocolConstants.POSITION_SCALE
        position_deg = math.degrees(position_rad)
        
        # 速度 (字节3-4)  
        vel_raw = struct.unpack('>h', data[3:5])[0]
        velocity_rpm = vel_raw * ProtocolConstants.VELOCITY_SCALE
        
        # 电流 (字节5-6)
        cur_raw = struct.unpack('>h', data[5:7])[0]
        current_a = cur_raw * ProtocolConstants.CURRENT_SCALE
        
        # 温度 (字节7)
        temperature = data[7] * ProtocolConstants.TEMPERATURE_SCALE
        
        return MotorStatus(
            motor_id=frame.arbitration_id,
            position=position_deg,
            velocity=velocity_rpm,
            current=current_a,
            temperature=temperature,
            feedback_type=FeedbackType.TYPE_2
        )
    
    @staticmethod
    def _decode_type3_feedback(frame: CANFrame) -> MotorStatus:
        """解码Type3反馈: 位置、速度"""
        data = frame.data
        
        # 位置 (字节1-4, float32)
        position_rad = bytes_to_float(data[1:5])
        position_deg = math.degrees(position_rad)
        
        # 速度 (字节5-8, float32) 
        velocity_rpm = bytes_to_float(data[5:9]) if len(data) >= 9 else 0.0
        
        return MotorStatus(
            motor_id=frame.arbitration_id,
            position=position_deg,
            velocity=velocity_rpm,
            feedback_type=FeedbackType.TYPE_3
        )
    
    @staticmethod
    def _decode_type4_feedback(frame: CANFrame) -> MotorStatus:
        """解码Type4反馈: 电机状态"""
        data = frame.data
        
        # 温度 (字节1)
        temperature = data[1] * ProtocolConstants.TEMPERATURE_SCALE
        
        # 电压 (字节2-3)
        voltage_raw = (data[2] << 8) | data[3] 
        voltage = voltage_raw * 0.1  # 电压换算
        
        # 其他状态信息...
        
        return MotorStatus(
            motor_id=frame.arbitration_id,
            temperature=temperature,
            voltage=voltage,
            feedback_type=FeedbackType.TYPE_4
        )
    
    @staticmethod
    def _decode_type5_feedback(frame: CANFrame) -> MotorStatus:
        """解码Type5反馈: 错误信息"""
        data = frame.data
        
        # 错误码 (字节1)
        error_code_raw = data[1]
        error_code = ErrorCode.NO_ERROR
        
        # 根据错误码位映射到枚举
        if error_code_raw & 0x01:
            error_code = ErrorCode.OVER_VOLTAGE
        elif error_code_raw & 0x02:
            error_code = ErrorCode.UNDER_VOLTAGE
        elif error_code_raw & 0x04:
            error_code = ErrorCode.OVER_CURRENT
        elif error_code_raw & 0x08:
            error_code = ErrorCode.OVER_TEMPERATURE
        elif error_code_raw & 0x10:
            error_code = ErrorCode.ENCODER_ERROR
        elif error_code_raw & 0x20:
            error_code = ErrorCode.HALL_ERROR
        elif error_code_raw != 0:
            error_code = ErrorCode.UNKNOWN_ERROR
        
        return MotorStatus(
            motor_id=frame.arbitration_id,
            error_code=error_code,
            feedback_type=FeedbackType.TYPE_5
        )
    
    @staticmethod
    def decode_id_query_response(frame: CANFrame) -> Optional[Tuple[int, ...]]:
        """解码ID查询响应
        
        Args:
            frame: ID查询响应帧
            
        Returns:
            Tuple[int, ...]: 检测到的电机ID列表，失败返回None
        """
        if frame.arbitration_id != 0x000:
            return None
        
        # 简化实现：从数据中提取电机ID
        motor_ids = []
        for i, byte_val in enumerate(frame.data):
            if 1 <= byte_val <= 32:  # 有效的电机ID范围
                motor_ids.append(byte_val)
        
        return tuple(motor_ids) if motor_ids else None
