"""
电机控制API层 (Motor Control API Layer)
======================================

提供面向对象的高级电机控制接口，封装复杂的协议细节，
为用户提供简洁易用的电机控制API。

主要功能：
- 电机实例管理
- 高级控制接口 (位置、速度、力矩控制)
- 状态监控和反馈
- 安全保护和错误处理
"""

import time
import threading
import logging
from typing import Optional, Callable, Dict, Any

try:
    from .hardware_layer import CANHardware
    from .protocol_layer import ProtocolEncoder, ProtocolDecoder
    from .data_types import (
        MotorStatus, ErrorCode, FeedbackType, ProtocolConstants, CANFrame
    )
except ImportError:
    from hardware_layer import CANHardware
    from protocol_layer import ProtocolEncoder, ProtocolDecoder
    from data_types import (
        MotorStatus, ErrorCode, FeedbackType, ProtocolConstants, CANFrame
    )


class Motor:
    """电机控制类
    
    提供完整的电机控制功能，包括位置控制、速度控制、力矩控制、
    状态监控、错误处理等。每个Motor实例对应一个物理电机。
    """
    
    def __init__(self, motor_id: int, can_hardware: CANHardware):
        """初始化电机控制实例
        
        Args:
            motor_id: 电机ID (1-32)
            can_hardware: CAN硬件接口
        """
        if not (1 <= motor_id <= 32):
            raise ValueError("电机ID必须在1-32范围内")
        
        self.motor_id = motor_id
        self.can_hardware = can_hardware
        self.encoder = ProtocolEncoder()
        self.decoder = ProtocolDecoder()
        
        # 电机状态
        self.last_status: Optional[MotorStatus] = None
        self.is_enabled = False
        self.last_command_time = 0.0
        
        # 安全参数
        self.max_position_deg = 360.0
        self.max_velocity_rpm = 1000.0
        self.max_current_a = 10.0
        self.max_torque_nm = 5.0
        
        # 回调函数
        self.status_callbacks: Dict[str, Callable[[MotorStatus], None]] = {}
        self.error_callbacks: Dict[str, Callable[[ErrorCode], None]] = {}
        
        # 日志
        self.logger = logging.getLogger(f"Motor.{motor_id}")
        
        # 注册CAN消息回调
        self.can_hardware.add_message_callback(self._on_can_message)
    
    def __del__(self):
        """析构函数，清理资源"""
        try:
            self.can_hardware.remove_message_callback(self._on_can_message)
        except:
            pass
    
    def set_zero_point(self, timeout: float = 2.0) -> bool:
        """设置电机零点
        
        Args:
            timeout: 操作超时时间(秒)
            
        Returns:
            bool: 设置成功返回True
        """
        try:
            frame = self.encoder.encode_set_zero_point(self.motor_id)
            success = self.can_hardware.send_frame(frame)
            
            if success:
                self.logger.info(f"电机{self.motor_id}零点设置指令已发送")
                # 等待500ms (协议要求的指令间隔)
                time.sleep(ProtocolConstants.COMMAND_INTERVAL_MS / 1000.0)
                return True
            else:
                self.logger.error(f"电机{self.motor_id}零点设置失败")
                return False
                
        except Exception as e:
            self.logger.error(f"设置零点异常: {e}")
            return False
    
    def set_position(self, position_deg: float, speed_limit_rpm: float = 100.0, 
                    current_limit_a: float = 5.0, mode: str = 'servo') -> bool:
        """设置目标位置
        
        Args:
            position_deg: 目标位置(度)
            speed_limit_rpm: 速度限制(RPM)
            current_limit_a: 电流限制(A)
            mode: 控制模式 ('servo' 或 'force')
            
        Returns:
            bool: 指令发送成功返回True
        """
        # 安全检查
        if not self._check_position_safe(position_deg):
            return False
        if not self._check_velocity_safe(speed_limit_rpm):
            return False
        if not self._check_current_safe(current_limit_a):
            return False
        
        try:
            if mode == 'servo':
                frame = self.encoder.encode_servo_position_command(
                    self.motor_id, position_deg, speed_limit_rpm, current_limit_a
                )
            elif mode == 'force':
                # 力位混控模式，需要更多参数
                frame = self.encoder.encode_force_position_command(
                    self.motor_id, 
                    kp=50.0,  # 默认刚度
                    kd=5.0,   # 默认阻尼
                    position=position_deg * 3.14159 / 180.0,  # 度转弧度
                    velocity=0.0,  # 无前馈速度
                    torque=0.0     # 无前馈力矩
                )
            else:
                raise ValueError(f"不支持的控制模式: {mode}")
            
            success = self.can_hardware.send_frame(frame)
            if success:
                self.last_command_time = time.time()
                self.logger.debug(f"电机{self.motor_id}位置指令: {position_deg}度")
                return True
            else:
                self.logger.error(f"电机{self.motor_id}位置指令发送失败")
                return False
                
        except Exception as e:
            self.logger.error(f"设置位置异常: {e}")
            return False
    
    def set_velocity(self, velocity_rpm: float, current_limit_a: float = 5.0) -> bool:
        """设置目标速度
        
        Args:
            velocity_rpm: 目标速度(RPM)
            current_limit_a: 电流限制(A)
            
        Returns:
            bool: 指令发送成功返回True
        """
        # 安全检查
        if not self._check_velocity_safe(velocity_rpm):
            return False
        if not self._check_current_safe(current_limit_a):
            return False
        
        try:
            frame = self.encoder.encode_servo_speed_command(
                self.motor_id, velocity_rpm, current_limit_a
            )
            
            success = self.can_hardware.send_frame(frame)
            if success:
                self.last_command_time = time.time()
                self.logger.debug(f"电机{self.motor_id}速度指令: {velocity_rpm}RPM")
                return True
            else:
                self.logger.error(f"电机{self.motor_id}速度指令发送失败")
                return False
                
        except Exception as e:
            self.logger.error(f"设置速度异常: {e}")
            return False
    
    def get_status(self, feedback_type: FeedbackType = FeedbackType.TYPE_1, 
                  timeout: float = 1.0) -> Optional[MotorStatus]:
        """获取电机状态
        
        Args:
            feedback_type: 反馈类型
            timeout: 超时时间(秒)
            
        Returns:
            MotorStatus: 电机状态，获取失败返回None
        """
        try:
            # 发送状态查询指令
            frame = self.encoder.encode_status_request(self.motor_id, feedback_type)
            success = self.can_hardware.send_frame(frame)
            
            if not success:
                self.logger.error(f"电机{self.motor_id}状态查询指令发送失败")
                return None
            
            # 等待响应
            start_time = time.time()
            while time.time() - start_time < timeout:
                response_frame = self.can_hardware.receive_frame(timeout=0.1)
                if response_frame and response_frame.arbitration_id == self.motor_id:
                    status = self.decoder.decode_feedback(response_frame)
                    if status:
                        self.last_status = status
                        return status
            
            self.logger.warning(f"电机{self.motor_id}状态查询超时")
            return None
            
        except Exception as e:
            self.logger.error(f"获取状态异常: {e}")
            return None
    
    def enable(self) -> bool:
        """使能电机"""
        self.is_enabled = True
        self.logger.info(f"电机{self.motor_id}已使能")
        return True
    
    def disable(self) -> bool:
        """失能电机"""
        self.is_enabled = False
        self.logger.info(f"电机{self.motor_id}已失能")
        return True
    
    def stop(self) -> bool:
        """急停电机"""
        try:
            # 发送零速度指令作为停止
            return self.set_velocity(0.0, 0.0)
        except Exception as e:
            self.logger.error(f"急停异常: {e}")
            return False
    
    def add_status_callback(self, name: str, callback: Callable[[MotorStatus], None]):
        """添加状态回调函数
        
        Args:
            name: 回调函数名称
            callback: 回调函数
        """
        self.status_callbacks[name] = callback
    
    def remove_status_callback(self, name: str):
        """移除状态回调函数"""
        if name in self.status_callbacks:
            del self.status_callbacks[name]
    
    def add_error_callback(self, name: str, callback: Callable[[ErrorCode], None]):
        """添加错误回调函数"""
        self.error_callbacks[name] = callback
    
    def remove_error_callback(self, name: str):
        """移除错误回调函数"""
        if name in self.error_callbacks:
            del self.error_callbacks[name]
    
    def _on_can_message(self, frame: CANFrame):
        """CAN消息回调处理
        
        Args:
            frame: 接收到的CAN帧
        """
        # 只处理本电机的消息
        if frame.arbitration_id != self.motor_id:
            return
        
        # 解码反馈消息
        status = self.decoder.decode_feedback(frame)
        if status:
            self.last_status = status
            
            # 调用状态回调
            for callback in self.status_callbacks.values():
                try:
                    callback(status)
                except Exception as e:
                    self.logger.error(f"状态回调执行失败: {e}")
            
            # 检查错误
            if status.has_error():
                self.logger.warning(f"电机{self.motor_id}错误: {status.get_error_description()}")
                
                # 调用错误回调
                for callback in self.error_callbacks.values():
                    try:
                        callback(status.error_code)
                    except Exception as e:
                        self.logger.error(f"错误回调执行失败: {e}")
    
    def _check_position_safe(self, position_deg: float) -> bool:
        """检查位置是否安全"""
        if abs(position_deg) > self.max_position_deg:
            self.logger.error(f"位置{position_deg}度超出安全范围±{self.max_position_deg}度")
            return False
        return True
    
    def _check_velocity_safe(self, velocity_rpm: float) -> bool:
        """检查速度是否安全"""
        if abs(velocity_rpm) > self.max_velocity_rpm:
            self.logger.error(f"速度{velocity_rpm}RPM超出安全范围±{self.max_velocity_rpm}RPM")
            return False
        return True
    
    def _check_current_safe(self, current_a: float) -> bool:
        """检查电流是否安全"""
        if current_a > self.max_current_a:
            self.logger.error(f"电流{current_a}A超出安全范围{self.max_current_a}A")
            return False
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """获取电机信息"""
        return {
            'motor_id': self.motor_id,
            'is_enabled': self.is_enabled,
            'last_status': self.last_status,
            'last_command_time': self.last_command_time,
            'safety_limits': {
                'max_position_deg': self.max_position_deg,
                'max_velocity_rpm': self.max_velocity_rpm,
                'max_current_a': self.max_current_a,
                'max_torque_nm': self.max_torque_nm
            }
        }
    
    def is_heartbeat_alive(self) -> bool:
        """检查心跳是否正常"""
        if self.last_command_time == 0:
            return True  # 还未发送过指令
        
        elapsed = time.time() - self.last_command_time
        return elapsed < (ProtocolConstants.HEARTBEAT_TIMEOUT_MS / 1000.0)


class MotorManager:
    """电机管理器
    
    管理多个电机实例，提供集中的控制和监控功能。
    """
    
    def __init__(self, can_hardware: CANHardware):
        """初始化电机管理器
        
        Args:
            can_hardware: CAN硬件接口
        """
        self.can_hardware = can_hardware
        self.motors: Dict[int, Motor] = {}
        self.logger = logging.getLogger("MotorManager")
    
    def add_motor(self, motor_id: int) -> Motor:
        """添加电机
        
        Args:
            motor_id: 电机ID
            
        Returns:
            Motor: 电机实例
        """
        if motor_id in self.motors:
            return self.motors[motor_id]
        
        motor = Motor(motor_id, self.can_hardware)
        self.motors[motor_id] = motor
        self.logger.info(f"添加电机{motor_id}")
        return motor
    
    def remove_motor(self, motor_id: int):
        """移除电机"""
        if motor_id in self.motors:
            del self.motors[motor_id]
            self.logger.info(f"移除电机{motor_id}")
    
    def get_motor(self, motor_id: int) -> Optional[Motor]:
        """获取电机实例"""
        return self.motors.get(motor_id)
    
    def scan_motors(self, timeout: float = 3.0) -> list[int]:
        """扫描总线上的电机
        
        Args:
            timeout: 扫描超时时间
            
        Returns:
            list[int]: 检测到的电机ID列表
        """
        try:
            # 发送ID查询指令
            frame = ProtocolEncoder.encode_query_id()
            success = self.can_hardware.send_frame(frame)
            
            if not success:
                self.logger.error("ID查询指令发送失败")
                return []
            
            # 收集响应
            detected_ids = set()
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                response_frame = self.can_hardware.receive_frame(timeout=0.1)
                if response_frame:
                    motor_ids = ProtocolDecoder.decode_id_query_response(response_frame)
                    if motor_ids:
                        detected_ids.update(motor_ids)
            
            detected_list = sorted(list(detected_ids))
            self.logger.info(f"检测到电机: {detected_list}")
            return detected_list
            
        except Exception as e:
            self.logger.error(f"扫描电机异常: {e}")
            return []
    
    def stop_all(self):
        """停止所有电机"""
        for motor in self.motors.values():
            motor.stop()
        self.logger.info("所有电机已停止")
    
    def get_all_status(self) -> Dict[int, Optional[MotorStatus]]:
        """获取所有电机状态"""
        status_dict = {}
        for motor_id, motor in self.motors.items():
            status_dict[motor_id] = motor.get_status()
        return status_dict
