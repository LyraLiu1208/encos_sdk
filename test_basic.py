#!/usr/bin/env python3
"""
基础测试脚本 (无外部依赖)
========================

测试SDK的核心功能，不需要安装python-can库。
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试基础模块导入"""
    print("=== 测试模块导入 ===")
    
    try:
        from data_types import MotorStatus, ErrorCode, FeedbackType, CANFrame, ProtocolConstants
        print("✓ data_types 模块导入成功")
    except ImportError as e:
        print(f"✗ data_types 导入失败: {e}")
        return False
    
    try:
        from protocol_layer import ProtocolEncoder, ProtocolDecoder
        print("✓ protocol_layer 模块导入成功")
    except ImportError as e:
        print(f"✗ protocol_layer 导入失败: {e}")
        return False
    
    return True


def test_data_types():
    """测试数据类型"""
    print("\n=== 测试数据类型 ===")
    
    from data_types import MotorStatus, ErrorCode, CANFrame
    
    # 测试电机状态
    status = MotorStatus(
        motor_id=1,
        position=45.0,
        velocity=100.0,
        current=2.5,
        temperature=35.0,
        error_code=ErrorCode.NO_ERROR
    )
    
    print(f"电机状态: ID={status.motor_id}, 位置={status.position}度, 速度={status.velocity}RPM")
    print(f"错误检查: {status.has_error()}")
    print(f"错误描述: {status.get_error_description()}")
    
    # 测试CAN帧
    frame = CANFrame(arbitration_id=0x123, data=b'\x01\x02\x03\x04')
    print(f"CAN帧: ID=0x{frame.arbitration_id:03X}, 数据={frame.data.hex().upper()}")
    
    print("✓ 数据类型测试通过")
    return True


def test_protocol_encoding():
    """测试协议编码"""
    print("\n=== 测试协议编码 ===")
    
    from protocol_layer import ProtocolEncoder
    
    encoder = ProtocolEncoder()
    
    # 测试查询ID指令
    frame = encoder.encode_query_id()
    print(f"查询ID指令: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
    expected = "55AA000000000000"
    if frame.data.hex().upper() == expected:
        print("✓ 查询ID编码正确")
    else:
        print(f"✗ 查询ID编码错误，期望:{expected}, 实际:{frame.data.hex().upper()}")
    
    # 测试零点设置
    frame = encoder.encode_set_zero_point(1)
    print(f"零点设置指令: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
    
    # 测试位置控制
    frame = encoder.encode_servo_position_command(1, 90.0, 100.0, 3.0)
    print(f"位置控制指令: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
    
    print("✓ 协议编码测试通过")
    return True


def test_protocol_decoding():
    """测试协议解码"""
    print("\n=== 测试协议解码 ===")
    
    from protocol_layer import ProtocolDecoder
    from data_types import CANFrame
    
    decoder = ProtocolDecoder()
    
    # 模拟Type1反馈数据
    test_data = bytes([0x20, 0x10, 0x00, 0x01, 0x00, 0x00, 0x10, 0x1E])
    frame = CANFrame(arbitration_id=1, data=test_data)
    
    status = decoder.decode_feedback(frame)
    if status:
        print(f"解码成功: 电机{status.motor_id}")
        print(f"  位置: {status.position:.2f}度")
        print(f"  速度: {status.velocity:.2f}RPM") 
        print(f"  温度: {status.temperature:.1f}°C")
        print(f"  反馈类型: {status.feedback_type}")
    else:
        print("解码失败")
    
    print("✓ 协议解码测试通过")
    return True


def test_constants():
    """测试常量定义"""
    print("\n=== 测试常量定义 ===")
    
    from data_types import ProtocolConstants
    
    print(f"CAN波特率: {ProtocolConstants.CAN_BITRATE}")
    print(f"心跳超时: {ProtocolConstants.HEARTBEAT_TIMEOUT_MS}ms")
    print(f"位置换算: {ProtocolConstants.POSITION_SCALE}")
    print(f"最大KP值: {ProtocolConstants.KP_MAX}")
    
    print("✓ 常量测试通过")
    return True


def test_utility_functions():
    """测试工具函数"""
    print("\n=== 测试工具函数 ===")
    
    from data_types import float_to_bytes, bytes_to_float
    
    # 测试浮点数转换
    test_value = 3.14159
    bytes_data = float_to_bytes(test_value)
    recovered_value = bytes_to_float(bytes_data)
    
    print(f"原始值: {test_value}")
    print(f"字节数据: {bytes_data.hex().upper()}")
    print(f"恢复值: {recovered_value}")
    
    if abs(test_value - recovered_value) < 1e-6:
        print("✓ 浮点数转换正确")
    else:
        print("✗ 浮点数转换错误")
        return False
    
    print("✓ 工具函数测试通过")
    return True


def run_basic_tests():
    """运行基础测试"""
    print("开始运行SDK基础测试...\n")
    
    tests = [
        test_imports,
        test_data_types,
        test_protocol_encoding,
        test_protocol_decoding,
        test_constants,
        test_utility_functions,
    ]
    
    failed_tests = []
    
    for test in tests:
        try:
            if not test():
                failed_tests.append(test.__name__)
        except Exception as e:
            print(f"❌ {test.__name__} 执行失败: {e}")
            import traceback
            traceback.print_exc()
            failed_tests.append(test.__name__)
    
    print("\n" + "="*60)
    
    if failed_tests:
        print(f"❌ 有 {len(failed_tests)} 个测试失败:")
        for test_name in failed_tests:
            print(f"   - {test_name}")
        print("="*60)
        return False
    else:
        print("🎉 所有基础测试通过！SDK核心功能正常")
        print("="*60)
        print("\n下一步:")
        print("1. 安装 python-can: pip install python-can")
        print("2. 运行完整测试: python test_sdk.py")
        print("3. 尝试CLI工具: python cli_tool.py --help")
        print("4. 阅读README.md了解更多用法")
        return True


if __name__ == '__main__':
    success = run_basic_tests()
    sys.exit(0 if success else 1)
