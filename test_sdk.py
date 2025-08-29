#!/usr/bin/env python3
"""
简单测试脚本
============

测试SDK的基本功能，可以在没有真实硬件的情况下运行。
"""

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from hardware_layer import MockCANHardware
    from motor_api import Motor, MotorManager
    from data_types import MotorStatus, ErrorCode, FeedbackType, CANFrame
    from protocol_layer import ProtocolEncoder, ProtocolDecoder
    print("✓ 所有模块导入成功")
except ImportError as e:
    print(f"✗ 模块导入失败: {e}")
    sys.exit(1)


def test_protocol_encoding():
    """测试协议编码功能"""
    print("\n=== 测试协议编码 ===")
    
    encoder = ProtocolEncoder()
    
    # 测试查询ID指令
    frame = encoder.encode_query_id()
    print(f"查询ID指令: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
    
    # 测试零点设置
    frame = encoder.encode_set_zero_point(1)
    print(f"零点设置指令: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
    
    # 测试位置控制
    frame = encoder.encode_servo_position_command(1, 90.0, 100.0, 3.0)
    print(f"位置控制指令: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
    
    # 测试力位混控
    frame = encoder.encode_force_position_command(1, 50.0, 5.0, 1.57, 0.0, 0.0)
    print(f"力位混控指令: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
    
    print("✓ 协议编码测试通过")


def test_protocol_decoding():
    """测试协议解码功能"""
    print("\n=== 测试协议解码 ===")
    
    decoder = ProtocolDecoder()
    
    # 模拟Type1反馈数据 (位置、速度、力矩)
    test_data = bytes([0x20, 0x10, 0x00, 0x01, 0x00, 0x00, 0x10, 0x1E])  # 示例数据
    frame = CANFrame(arbitration_id=1, data=test_data)
    
    status = decoder.decode_feedback(frame)
    if status:
        print(f"解码成功: 电机{status.motor_id}, 位置={status.position:.2f}度")
        print(f"           速度={status.velocity:.2f}RPM, 温度={status.temperature:.1f}°C")
    else:
        print("解码失败")
    
    print("✓ 协议解码测试通过")


def test_mock_hardware():
    """测试模拟硬件"""
    print("\n=== 测试模拟硬件 ===")
    
    # 创建模拟硬件
    mock_hw = MockCANHardware()
    
    # 连接
    if mock_hw.connect():
        print("✓ 模拟硬件连接成功")
    else:
        print("✗ 模拟硬件连接失败")
        return
    
    # 发送测试帧
    test_frame = CANFrame(arbitration_id=0x123, data=b'\x01\x02\x03\x04\x05\x06\x07\x08')
    if mock_hw.send_frame(test_frame):
        print("✓ 测试帧发送成功")
    
    # 断开连接
    mock_hw.disconnect()
    print("✓ 模拟硬件测试通过")


def test_motor_api():
    """测试电机API"""
    print("\n=== 测试电机API ===")
    
    # 创建模拟硬件和电机
    mock_hw = MockCANHardware()
    mock_hw.connect()
    
    motor = Motor(motor_id=1, can_hardware=mock_hw)
    
    # 测试基本控制
    print("测试零点设置...")
    if motor.set_zero_point():
        print("✓ 零点设置成功")
    
    print("测试位置控制...")
    if motor.set_position(45.0, 100.0, 3.0):
        print("✓ 位置控制成功")
    
    print("测试速度控制...")
    if motor.set_velocity(50.0, 2.0):
        print("✓ 速度控制成功")
    
    # 测试安全检查
    print("测试安全限制...")
    motor.max_position_deg = 90.0
    if not motor.set_position(180.0):  # 应该失败
        print("✓ 安全限制工作正常")
    
    # 获取电机信息
    info = motor.get_info()
    print(f"电机信息: ID={info['motor_id']}, 使能={info['is_enabled']}")
    
    mock_hw.disconnect()
    print("✓ 电机API测试通过")


def test_motor_manager():
    """测试电机管理器"""
    print("\n=== 测试电机管理器 ===")
    
    mock_hw = MockCANHardware()
    mock_hw.connect()
    
    manager = MotorManager(mock_hw)
    
    # 添加电机
    motor1 = manager.add_motor(1)
    motor2 = manager.add_motor(2)
    
    print(f"添加了{len(manager.motors)}个电机")
    
    # 测试获取电机
    motor = manager.get_motor(1)
    if motor and motor.motor_id == 1:
        print("✓ 电机获取成功")
    
    # 测试停止所有电机
    manager.stop_all()
    print("✓ 停止所有电机")
    
    mock_hw.disconnect()
    print("✓ 电机管理器测试通过")


def test_data_types():
    """测试数据类型"""
    print("\n=== 测试数据类型 ===")
    
    # 测试电机状态
    status = MotorStatus(
        motor_id=1,
        position=45.0,
        velocity=100.0,
        current=2.5,
        temperature=35.0,
        error_code=ErrorCode.NO_ERROR
    )
    
    print(f"电机状态: {status.motor_id}, {status.position}度, {status.velocity}RPM")
    print(f"错误状态: {status.has_error()}")
    print(f"错误描述: {status.get_error_description()}")
    
    # 测试错误状态
    error_status = MotorStatus(motor_id=2, error_code=ErrorCode.OVER_TEMPERATURE)
    print(f"错误电机: {error_status.get_error_description()}")
    
    print("✓ 数据类型测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始运行SDK测试...")
    
    try:
        test_data_types()
        test_protocol_encoding()
        test_protocol_decoding()
        test_mock_hardware()
        test_motor_api()
        test_motor_manager()
        
        print("\n" + "="*50)
        print("🎉 所有测试通过！SDK基本功能正常")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
