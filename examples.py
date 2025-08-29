"""
使用示例
========

演示如何使用电机控制SDK的各种功能。
"""

import time
import logging
from encos_sdk import CANHardware, Motor, MotorManager, FeedbackType

# 配置日志
logging.basicConfig(level=logging.INFO)


def example_basic_control():
    """基本控制示例"""
    print("=== 基本电机控制示例 ===")
    
    # 初始化CAN硬件
    with CANHardware(interface='socketcan', channel='can0') as can_hw:
        if not can_hw.is_connected:
            print("CAN硬件连接失败，使用模拟硬件")
            from encos_sdk.hardware_layer import MockCANHardware
            can_hw = MockCANHardware()
            can_hw.connect()
        
        # 创建电机实例
        motor = Motor(motor_id=1, can_hardware=can_hw)
        
        # 设置零点
        print("设置零点...")
        motor.set_zero_point()
        
        # 位置控制
        print("位置控制到90度...")
        motor.set_position(90.0, speed_limit_rpm=100.0, current_limit_a=3.0)
        
        time.sleep(2)
        
        # 获取状态
        print("获取电机状态...")
        status = motor.get_status(FeedbackType.TYPE_1)
        if status:
            print(f"当前位置: {status.position:.2f}度")
            print(f"当前速度: {status.velocity:.2f}RPM")
            print(f"温度: {status.temperature:.1f}°C")
        
        # 速度控制
        print("速度控制到50RPM...")
        motor.set_velocity(50.0, current_limit_a=2.0)
        
        time.sleep(2)
        
        # 停止电机
        print("停止电机...")
        motor.stop()


def example_multiple_motors():
    """多电机控制示例"""
    print("\n=== 多电机控制示例 ===")
    
    with CANHardware(interface='socketcan', channel='can0') as can_hw:
        if not can_hw.is_connected:
            from encos_sdk.hardware_layer import MockCANHardware
            can_hw = MockCANHardware()
            can_hw.connect()
        
        # 创建电机管理器
        manager = MotorManager(can_hw)
        
        # 扫描电机
        print("扫描总线上的电机...")
        motor_ids = manager.scan_motors()
        print(f"检测到电机: {motor_ids}")
        
        # 如果没有检测到电机，使用默认ID
        if not motor_ids:
            motor_ids = [1, 2]
            print(f"使用默认电机ID: {motor_ids}")
        
        # 添加电机
        motors = []
        for motor_id in motor_ids[:2]:  # 最多控制2个电机
            motor = manager.add_motor(motor_id)
            motors.append(motor)
        
        # 同时控制多个电机
        print("同时控制多个电机...")
        for i, motor in enumerate(motors):
            angle = 45.0 + i * 45.0  # 不同角度
            motor.set_position(angle, speed_limit_rpm=80.0)
            print(f"电机{motor.motor_id}目标位置: {angle}度")
        
        time.sleep(3)
        
        # 获取所有电机状态
        print("获取所有电机状态...")
        all_status = manager.get_all_status()
        for motor_id, status in all_status.items():
            if status:
                print(f"电机{motor_id}: 位置={status.position:.2f}度, "
                      f"速度={status.velocity:.2f}RPM")
        
        # 停止所有电机
        print("停止所有电机...")
        manager.stop_all()


def example_status_monitoring():
    """状态监控示例"""
    print("\n=== 状态监控示例 ===")
    
    with CANHardware(interface='socketcan', channel='can0') as can_hw:
        if not can_hw.is_connected:
            from encos_sdk.hardware_layer import MockCANHardware
            can_hw = MockCANHardware()
            can_hw.connect()
        
        motor = Motor(motor_id=1, can_hardware=can_hw)
        
        # 添加状态回调
        def on_status_update(status):
            print(f"状态更新: 位置={status.position:.2f}度, "
                  f"速度={status.velocity:.2f}RPM")
        
        def on_error(error_code):
            print(f"电机错误: {error_code}")
        
        motor.add_status_callback("demo", on_status_update)
        motor.add_error_callback("demo", on_error)
        
        # 开始运动
        print("开始运动，监控状态变化...")
        motor.set_position(180.0, speed_limit_rpm=60.0)
        
        # 监控一段时间
        for i in range(10):
            status = motor.get_status()
            if status:
                print(f"第{i+1}次查询: {status.position:.2f}度")
            time.sleep(0.5)
        
        motor.stop()


def example_safety_features():
    """安全功能示例"""
    print("\n=== 安全功能示例 ===")
    
    with CANHardware(interface='socketcan', channel='can0') as can_hw:
        if not can_hw.is_connected:
            from encos_sdk.hardware_layer import MockCANHardware
            can_hw = MockCANHardware()
            can_hw.connect()
        
        motor = Motor(motor_id=1, can_hardware=can_hw)
        
        # 设置安全限制
        motor.max_position_deg = 90.0
        motor.max_velocity_rpm = 200.0
        motor.max_current_a = 3.0
        
        print("测试安全限制...")
        
        # 尝试超出位置限制
        print("尝试设置超出限制的位置(180度)...")
        success = motor.set_position(180.0)  # 应该失败
        print(f"结果: {'成功' if success else '失败(符合预期)'}")
        
        # 尝试超出速度限制
        print("尝试设置超出限制的速度(500RPM)...")
        success = motor.set_velocity(500.0)  # 应该失败
        print(f"结果: {'成功' if success else '失败(符合预期)'}")
        
        # 正常范围内的控制
        print("设置正常范围内的位置(45度)...")
        success = motor.set_position(45.0)
        print(f"结果: {'成功' if success else '失败'}")
        
        # 检查心跳
        print(f"心跳状态: {'正常' if motor.is_heartbeat_alive() else '异常'}")


def example_force_position_control():
    """力位混控示例"""
    print("\n=== 力位混控示例 ===")
    
    with CANHardware(interface='socketcan', channel='can0') as can_hw:
        if not can_hw.is_connected:
            from encos_sdk.hardware_layer import MockCANHardware
            can_hw = MockCANHardware()
            can_hw.connect()
        
        motor = Motor(motor_id=1, can_hardware=can_hw)
        
        print("使用力位混控模式...")
        
        # 力位混控 - 柔顺控制
        print("柔顺位置控制(低刚度)...")
        motor.set_position(60.0, speed_limit_rpm=80.0, mode='force')
        
        time.sleep(2)
        
        # 获取状态
        status = motor.get_status(FeedbackType.TYPE_1)  # Type1包含力矩信息
        if status:
            print(f"位置: {status.position:.2f}度")
            print(f"力矩: {status.torque:.3f}N·m")
        
        motor.stop()


if __name__ == '__main__':
    """运行所有示例"""
    try:
        example_basic_control()
        example_multiple_motors()
        example_status_monitoring()
        example_safety_features()
        example_force_position_control()
        
        print("\n=== 所有示例完成 ===")
        
    except KeyboardInterrupt:
        print("\n示例被用户中断")
    except Exception as e:
        print(f"\n示例运行出错: {e}")
        import traceback
        traceback.print_exc()
