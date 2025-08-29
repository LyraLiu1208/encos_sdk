#!/usr/bin/env python3
"""
命令行工具 (CLI Tool)
====================

提供完整的电机控制命令行界面，支持电机配置、控制、监控等功能。
这是SDK的用户交互层，适合用于硬件调试和自动化测试。

支持的命令：
- scan: 扫描总线上的电机
- zero <motor_id>: 设置电机零点
- pos <motor_id> <angle> [speed] [current]: 位置控制
- vel <motor_id> <speed> [current]: 速度控制  
- status <motor_id>: 获取电机状态
- monitor <motor_id>: 实时监控电机状态
- config: 显示和设置配置参数
"""

import argparse
import sys
import time
import signal
import logging
from typing import Optional

try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # 定义空的颜色常量
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

# 导入SDK模块
try:
    from . import CANHardware, Motor, MotorManager, MotorStatus, ErrorCode, FeedbackType
except ImportError:
    # 直接运行时的导入方式
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hardware_layer import CANHardware
    from motor_api import Motor, MotorManager
    from data_types import MotorStatus, ErrorCode, FeedbackType


class MotorCLI:
    """电机控制命令行工具"""
    
    def __init__(self):
        self.can_hardware: Optional[CANHardware] = None
        self.motor_manager: Optional[MotorManager] = None
        self.is_running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("MotorCLI")
    
    def _signal_handler(self, signum, frame):
        """信号处理函数 (Ctrl+C)"""
        self.print_colored("\n\n正在停止程序...", Fore.YELLOW)
        self.is_running = False
        if self.motor_manager:
            self.motor_manager.stop_all()
        if self.can_hardware:
            self.can_hardware.disconnect()
        sys.exit(0)
    
    def print_colored(self, text: str, color: str = "", style: str = ""):
        """彩色打印"""
        if COLORS_AVAILABLE:
            print(f"{style}{color}{text}{Style.RESET_ALL}")
        else:
            print(text)
    
    def init_hardware(self, interface: str = 'socketcan', channel: str = 'can0', 
                     bitrate: int = 1000000) -> bool:
        """初始化CAN硬件"""
        try:
            self.print_colored(f"正在初始化CAN硬件: {interface}:{channel} @ {bitrate}bps", Fore.CYAN)
            
            self.can_hardware = CANHardware(interface, channel, bitrate)
            if not self.can_hardware.connect():
                self.print_colored("CAN硬件连接失败", Fore.RED)
                return False
            
            self.motor_manager = MotorManager(self.can_hardware)
            self.print_colored("CAN硬件初始化成功", Fore.GREEN)
            return True
            
        except Exception as e:
            self.print_colored(f"硬件初始化失败: {e}", Fore.RED)
            return False
    
    def cmd_scan(self, args) -> int:
        """扫描总线上的电机"""
        if not self.motor_manager:
            self.print_colored("请先初始化硬件", Fore.RED)
            return 1
        
        self.print_colored("正在扫描电机...", Fore.CYAN)
        
        motor_ids = self.motor_manager.scan_motors(timeout=args.timeout)
        
        if motor_ids:
            self.print_colored(f"\n检测到 {len(motor_ids)} 个电机:", Fore.GREEN, Style.BRIGHT)
            for motor_id in motor_ids:
                self.print_colored(f"  电机ID: {motor_id}", Fore.WHITE)
        else:
            self.print_colored("未检测到电机", Fore.YELLOW)
        
        return 0
    
    def cmd_zero(self, args) -> int:
        """设置电机零点"""
        if not self.motor_manager:
            self.print_colored("请先初始化硬件", Fore.RED)
            return 1
        
        motor = self.motor_manager.add_motor(args.motor_id)
        
        self.print_colored(f"正在设置电机{args.motor_id}零点...", Fore.CYAN)
        
        if motor.set_zero_point():
            self.print_colored(f"电机{args.motor_id}零点设置成功", Fore.GREEN)
            return 0
        else:
            self.print_colored(f"电机{args.motor_id}零点设置失败", Fore.RED)
            return 1
    
    def cmd_position(self, args) -> int:
        """位置控制"""
        if not self.motor_manager:
            self.print_colored("请先初始化硬件", Fore.RED)
            return 1
        
        motor = self.motor_manager.add_motor(args.motor_id)
        
        self.print_colored(
            f"电机{args.motor_id} 位置控制: {args.angle}度, "
            f"速度限制: {args.speed}RPM, 电流限制: {args.current}A", 
            Fore.CYAN
        )
        
        if motor.set_position(args.angle, args.speed, args.current, args.mode):
            self.print_colored("位置指令发送成功", Fore.GREEN)
            return 0
        else:
            self.print_colored("位置指令发送失败", Fore.RED)
            return 1
    
    def cmd_velocity(self, args) -> int:
        """速度控制"""
        if not self.motor_manager:
            self.print_colored("请先初始化硬件", Fore.RED)
            return 1
        
        motor = self.motor_manager.add_motor(args.motor_id)
        
        self.print_colored(
            f"电机{args.motor_id} 速度控制: {args.speed}RPM, "
            f"电流限制: {args.current}A", 
            Fore.CYAN
        )
        
        if motor.set_velocity(args.speed, args.current):
            self.print_colored("速度指令发送成功", Fore.GREEN)
            return 0
        else:
            self.print_colored("速度指令发送失败", Fore.RED)
            return 1
    
    def cmd_status(self, args) -> int:
        """获取电机状态"""
        if not self.motor_manager:
            self.print_colored("请先初始化硬件", Fore.RED)
            return 1
        
        motor = self.motor_manager.add_motor(args.motor_id)
        
        self.print_colored(f"正在获取电机{args.motor_id}状态...", Fore.CYAN)
        
        status = motor.get_status(FeedbackType(args.type))
        
        if status:
            self._print_status(status)
            return 0
        else:
            self.print_colored("获取状态失败", Fore.RED)
            return 1
    
    def cmd_monitor(self, args) -> int:
        """实时监控电机状态"""
        if not self.motor_manager:
            self.print_colored("请先初始化硬件", Fore.RED)
            return 1
        
        motor = self.motor_manager.add_motor(args.motor_id)
        
        self.print_colored(f"开始监控电机{args.motor_id} (按Ctrl+C停止)", Fore.CYAN, Style.BRIGHT)
        self.print_colored("=" * 60, Fore.WHITE)
        
        try:
            while self.is_running:
                status = motor.get_status(FeedbackType(args.type))
                
                if status:
                    # 清屏并打印状态 (仅在终端支持时)
                    if hasattr(os, 'system'):
                        os.system('clear' if os.name == 'posix' else 'cls')
                    
                    self.print_colored(f"电机{args.motor_id}实时状态", Fore.CYAN, Style.BRIGHT)
                    self.print_colored("=" * 60, Fore.WHITE)
                    self._print_status(status)
                    self.print_colored("=" * 60, Fore.WHITE)
                    self.print_colored("按Ctrl+C停止监控", Fore.YELLOW)
                else:
                    self.print_colored(".", Fore.YELLOW, end="", flush=True)
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            self.print_colored("\n监控已停止", Fore.YELLOW)
        
        return 0
    
    def cmd_config(self, args) -> int:
        """配置管理"""
        if args.list:
            self._print_config()
        elif args.set:
            # 解析设置参数 (key=value格式)
            try:
                key, value = args.set.split('=', 1)
                self._set_config(key.strip(), value.strip())
            except ValueError:
                self.print_colored("配置格式错误，请使用 key=value 格式", Fore.RED)
                return 1
        else:
            self._print_config()
        
        return 0
    
    def _print_status(self, status: MotorStatus):
        """打印电机状态"""
        self.print_colored(f"电机ID: {status.motor_id}", Fore.WHITE, Style.BRIGHT)
        self.print_colored(f"位置: {status.position:.2f}°", Fore.GREEN)
        self.print_colored(f"速度: {status.velocity:.2f} RPM", Fore.GREEN)
        
        if status.current != 0:
            self.print_colored(f"电流: {status.current:.2f} A", Fore.GREEN)
        
        if status.torque != 0:
            self.print_colored(f"力矩: {status.torque:.3f} N·m", Fore.GREEN)
        
        self.print_colored(f"温度: {status.temperature:.1f}°C", Fore.BLUE)
        
        if status.voltage != 0:
            self.print_colored(f"电压: {status.voltage:.1f} V", Fore.BLUE)
        
        # 错误状态
        if status.has_error():
            self.print_colored(f"错误: {status.get_error_description()}", Fore.RED, Style.BRIGHT)
        else:
            self.print_colored("状态: 正常", Fore.GREEN)
        
        self.print_colored(f"反馈类型: Type {status.feedback_type.value if status.feedback_type else 'Unknown'}", Fore.CYAN)
    
    def _print_config(self):
        """打印当前配置"""
        self.print_colored("当前配置:", Fore.CYAN, Style.BRIGHT)
        
        if self.can_hardware:
            stats = self.can_hardware.get_statistics()
            for key, value in stats.items():
                self.print_colored(f"  {key}: {value}", Fore.WHITE)
        else:
            self.print_colored("  CAN硬件未初始化", Fore.YELLOW)
    
    def _set_config(self, key: str, value: str):
        """设置配置参数"""
        self.print_colored(f"设置 {key} = {value}", Fore.CYAN)
        # TODO: 实现配置设置逻辑
        self.print_colored("配置设置功能待实现", Fore.YELLOW)


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='motor_cli',
        description='电机控制命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --interface socketcan --channel can0 scan          # 扫描电机
  %(prog)s --interface pcan --channel PCAN_USBBUS1 scan       # 使用PCAN接口
  %(prog)s zero 1                                            # 设置电机1零点
  %(prog)s pos 1 90                                          # 电机1转到90度
  %(prog)s pos 1 -45 200 3.0 --mode servo                    # 高级位置控制
  %(prog)s vel 1 100 2.0                                     # 电机1速度100RPM
  %(prog)s status 1                                          # 获取电机1状态
  %(prog)s monitor 1 --interval 0.1                          # 监控电机1
  %(prog)s config --list                                     # 显示配置

CAN接口类型:
  socketcan    - Linux SocketCAN接口 (默认)
  pcan         - Peak PCAN接口  
  vector       - Vector接口
  kvaser       - Kvaser接口
  
常见通道名称:
  socketcan: can0, can1, vcan0
  pcan: PCAN_USBBUS1, PCAN_USBBUS2
        """
    )
    
    # 全局参数
    parser.add_argument('--interface', default='socketcan', 
                       help='CAN接口类型 (默认: socketcan)')
    parser.add_argument('--channel', default='can0',
                       help='CAN通道名称 (默认: can0)')
    parser.add_argument('--bitrate', type=int, default=1000000,
                       help='CAN波特率 (默认: 1000000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # scan命令
    scan_parser = subparsers.add_parser('scan', help='扫描总线上的电机')
    scan_parser.add_argument('--timeout', type=float, default=3.0,
                           help='扫描超时时间 (默认: 3.0秒)')
    
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
    pos_parser.add_argument('--mode', choices=['servo', 'force'], default='servo',
                          help='控制模式 (默认: servo)')
    
    # vel命令
    vel_parser = subparsers.add_parser('vel', help='速度控制')
    vel_parser.add_argument('motor_id', type=int, help='电机ID')
    vel_parser.add_argument('speed', type=float, help='目标速度 (RPM)')
    vel_parser.add_argument('current', type=float, nargs='?', default=5.0,
                          help='电流限制 (A, 默认: 5.0)')
    
    # status命令
    status_parser = subparsers.add_parser('status', help='获取电机状态')
    status_parser.add_argument('motor_id', type=int, help='电机ID')
    status_parser.add_argument('--type', type=int, choices=[1,2,3,4,5], default=1,
                             help='反馈类型 (1-5, 默认: 1)')
    
    # monitor命令
    monitor_parser = subparsers.add_parser('monitor', help='实时监控电机状态')
    monitor_parser.add_argument('motor_id', type=int, help='电机ID')
    monitor_parser.add_argument('--interval', type=float, default=0.5,
                              help='监控间隔 (秒, 默认: 0.5)')
    monitor_parser.add_argument('--type', type=int, choices=[1,2,3,4,5], default=1,
                              help='反馈类型 (1-5, 默认: 1)')
    
    # config命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_group = config_parser.add_mutually_exclusive_group()
    config_group.add_argument('--list', action='store_true', help='显示当前配置')
    config_group.add_argument('--set', help='设置配置 (格式: key=value)')
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建CLI实例
    cli = MotorCLI()
    
    # 检查是否需要CAN硬件
    hardware_commands = ['scan', 'zero', 'pos', 'vel', 'status', 'monitor']
    
    if args.command in hardware_commands:
        if not cli.init_hardware(args.interface, args.channel, args.bitrate):
            return 1
    
    # 执行命令
    try:
        if args.command == 'scan':
            return cli.cmd_scan(args)
        elif args.command == 'zero':
            return cli.cmd_zero(args)
        elif args.command == 'pos':
            return cli.cmd_position(args)
        elif args.command == 'vel':
            return cli.cmd_velocity(args)
        elif args.command == 'status':
            return cli.cmd_status(args)
        elif args.command == 'monitor':
            return cli.cmd_monitor(args)
        elif args.command == 'config':
            return cli.cmd_config(args)
        else:
            parser.print_help()
            return 0
            
    except Exception as e:
        cli.print_colored(f"命令执行失败: {e}", Fore.RED)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    finally:
        # 清理资源
        if cli.can_hardware:
            cli.can_hardware.disconnect()


if __name__ == '__main__':
    sys.exit(main())
