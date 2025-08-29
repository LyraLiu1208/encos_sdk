#!/usr/bin/env python3
"""
简单CLI演示工具
===============

展示CLI工具的基本功能，不需要安装python-can库。
"""

import argparse
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_scan():
    """演示扫描功能"""
    print("=== 扫描电机演示 ===")
    print("正在扫描总线上的电机...")
    print("检测到以下电机:")
    print("  电机ID: 1")
    print("  电机ID: 2")
    print("✓ 扫描完成")

def demo_zero(motor_id):
    """演示零点设置"""
    print(f"=== 电机{motor_id}零点设置演示 ===")
    print(f"正在设置电机{motor_id}零点...")
    print("发送零点设置指令...")
    print(f"✓ 电机{motor_id}零点设置成功")

def demo_position(motor_id, angle, speed, current):
    """演示位置控制"""
    print(f"=== 电机{motor_id}位置控制演示 ===")
    print(f"目标位置: {angle}度")
    print(f"速度限制: {speed}RPM")
    print(f"电流限制: {current}A")
    print("发送位置控制指令...")
    print(f"✓ 电机{motor_id}位置指令发送成功")

def demo_velocity(motor_id, speed, current):
    """演示速度控制"""
    print(f"=== 电机{motor_id}速度控制演示 ===")
    print(f"目标速度: {speed}RPM")
    print(f"电流限制: {current}A")
    print("发送速度控制指令...")
    print(f"✓ 电机{motor_id}速度指令发送成功")

def demo_status(motor_id):
    """演示状态获取"""
    print(f"=== 电机{motor_id}状态查询演示 ===")
    print("正在获取电机状态...")
    print("电机状态:")
    print(f"  电机ID: {motor_id}")
    print(f"  位置: 45.2度")
    print(f"  速度: 123.5 RPM")
    print(f"  电流: 2.3 A")
    print(f"  温度: 35.6°C")
    print(f"  状态: 正常")
    print("✓ 状态获取成功")

def demo_monitor(motor_id, interval):
    """演示监控功能"""
    print(f"=== 电机{motor_id}监控演示 ===")
    print(f"监控间隔: {interval}秒")
    print("开始实时监控 (这里只是演示，实际会持续更新)")
    print("=" * 60)
    
    # 模拟几次数据更新
    import time
    for i in range(3):
        print(f"时间: {i+1}s")
        print(f"电机{motor_id}实时状态")
        print(f"  位置: {45.0 + i*10:.1f}度")
        print(f"  速度: {100.0 + i*20:.1f} RPM")
        print(f"  电流: {2.0 + i*0.5:.1f} A")
        print(f"  温度: 35.{i}°C")
        print("  状态: 正常")
        print("-" * 40)
        if i < 2:
            time.sleep(1)
    
    print("监控演示结束 (按Ctrl+C可停止实际监控)")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        prog='demo_cli',
        description='电机控制CLI工具演示',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python demo_cli.py scan                     # 扫描电机
  python demo_cli.py zero 1                   # 设置电机1零点
  python demo_cli.py pos 1 90                 # 电机1转到90度
  python demo_cli.py pos 1 -45 200 3.0        # 高级位置控制
  python demo_cli.py vel 1 100 2.0             # 电机1速度100RPM
  python demo_cli.py status 1                  # 获取电机1状态
  python demo_cli.py monitor 1 --interval 0.5  # 监控电机1

注意: 这是演示版本，实际功能需要安装python-can库。
        """
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # scan命令
    subparsers.add_parser('scan', help='扫描总线上的电机')
    
    # zero命令
    zero_parser = subparsers.add_parser('zero', help='设置电机零点')
    zero_parser.add_argument('motor_id', type=int, help='电机ID')
    
    # pos命令
    pos_parser = subparsers.add_parser('pos', help='位置控制')
    pos_parser.add_argument('motor_id', type=int, help='电机ID')
    pos_parser.add_argument('angle', type=float, help='目标角度 (度)')
    pos_parser.add_argument('speed', type=float, nargs='?', default=100.0,
                          help='速度限制 (RPM, 默认: 100)')
    pos_parser.add_argument('current', type=float, nargs='?', default=5.0,
                          help='电流限制 (A, 默认: 5.0)')
    
    # vel命令
    vel_parser = subparsers.add_parser('vel', help='速度控制')
    vel_parser.add_argument('motor_id', type=int, help='电机ID')
    vel_parser.add_argument('speed', type=float, help='目标速度 (RPM)')
    vel_parser.add_argument('current', type=float, nargs='?', default=5.0,
                          help='电流限制 (A, 默认: 5.0)')
    
    # status命令
    status_parser = subparsers.add_parser('status', help='获取电机状态')
    status_parser.add_argument('motor_id', type=int, help='电机ID')
    
    # monitor命令
    monitor_parser = subparsers.add_parser('monitor', help='实时监控电机状态')
    monitor_parser.add_argument('motor_id', type=int, help='电机ID')
    monitor_parser.add_argument('--interval', type=float, default=0.5,
                              help='监控间隔 (秒, 默认: 0.5)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    print(f"电机控制CLI工具演示 - 命令: {args.command}")
    print("=" * 50)
    
    try:
        if args.command == 'scan':
            demo_scan()
        elif args.command == 'zero':
            demo_zero(args.motor_id)
        elif args.command == 'pos':
            demo_position(args.motor_id, args.angle, args.speed, args.current)
        elif args.command == 'vel':
            demo_velocity(args.motor_id, args.speed, args.current)
        elif args.command == 'status':
            demo_status(args.motor_id)
        elif args.command == 'monitor':
            demo_monitor(args.motor_id, args.interval)
        
        print("\n" + "=" * 50)
        print("演示完成！")
        print("\n要使用真实功能:")
        print("1. 安装依赖: pip install python-can colorama")
        print("2. 运行真实CLI: python cli_tool.py --help")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
        return 0
    except Exception as e:
        print(f"演示失败: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
