"""
硬件通信层 (Hardware Communication Layer)
==========================================

负责与USB-CAN分析仪硬件直接交互，处理CAN总线的初始化、数据发送和接收。
这一层抽象了不同CAN硬件的差异，为上层提供统一的接口。

主要功能：
- CAN总线初始化和配置
- CAN数据帧的发送和接收
- 硬件状态监控
- 错误处理和重连机制
"""

import can
import time
import threading
import logging
from typing import Optional, Callable, List
from queue import Queue, Empty

try:
    from .data_types import CANFrame, ProtocolConstants
except ImportError:
    from data_types import CANFrame, ProtocolConstants


class CANHardware:
    """CAN硬件通信类
    
    封装python-can库，提供简洁的CAN通信接口。
    支持多种CAN适配器，包括但不限于：
    - SocketCAN (Linux)
    - PCAN (Peak)
    - Vector
    - Kvaser
    """
    
    def __init__(self, interface: str = 'socketcan', channel: str = 'can0', 
                 bitrate: int = ProtocolConstants.CAN_BITRATE):
        """初始化CAN硬件
        
        Args:
            interface: CAN接口类型 ('socketcan', 'pcan', 'vector', 'kvaser' 等)
            channel: CAN通道名称 (如 'can0', 'PCAN_USBBUS1' 等)
            bitrate: CAN波特率 (默认1Mbps)
        """
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus: Optional[can.Bus] = None
        self.is_connected = False
        
        # 接收线程和队列
        self._receive_thread: Optional[threading.Thread] = None
        self._stop_receive = threading.Event()
        self._receive_queue = Queue()
        self._message_callbacks: List[Callable[[CANFrame], None]] = []
        
        # 日志
        self.logger = logging.getLogger(f"CANHardware.{channel}")
        
    def connect(self) -> bool:
        """连接CAN总线
        
        Returns:
            bool: 连接成功返回True，否则返回False
        """
        try:
            self.bus = can.Bus(
                interface=self.interface,
                channel=self.channel,
                bitrate=self.bitrate
            )
            self.is_connected = True
            self.logger.info(f"CAN总线连接成功: {self.interface}:{self.channel} @ {self.bitrate}bps")
            
            # 启动接收线程
            self._start_receive_thread()
            return True
            
        except Exception as e:
            self.logger.error(f"CAN总线连接失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开CAN总线连接"""
        self._stop_receive_thread()
        
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            
        self.is_connected = False
        self.logger.info("CAN总线已断开")
    
    def send_frame(self, frame: CANFrame, timeout: float = 1.0) -> bool:
        """发送CAN数据帧
        
        Args:
            frame: 要发送的CAN帧
            timeout: 发送超时时间(秒)
            
        Returns:
            bool: 发送成功返回True，否则返回False
        """
        if not self.is_connected or not self.bus:
            self.logger.error("CAN总线未连接")
            return False
        
        try:
            msg = can.Message(
                arbitration_id=frame.arbitration_id,
                data=frame.data,
                is_extended_id=frame.is_extended
            )
            
            self.bus.send(msg, timeout=timeout)
            self.logger.debug(f"发送CAN帧: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送CAN帧失败: {e}")
            return False
    
    def receive_frame(self, timeout: float = 0.1) -> Optional[CANFrame]:
        """从队列中接收CAN数据帧
        
        Args:
            timeout: 接收超时时间(秒)
            
        Returns:
            CANFrame: 接收到的CAN帧，超时返回None
        """
        try:
            return self._receive_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def add_message_callback(self, callback: Callable[[CANFrame], None]):
        """添加消息回调函数
        
        Args:
            callback: 当接收到CAN帧时调用的回调函数
        """
        self._message_callbacks.append(callback)
    
    def remove_message_callback(self, callback: Callable[[CANFrame], None]):
        """移除消息回调函数"""
        if callback in self._message_callbacks:
            self._message_callbacks.remove(callback)
    
    def _start_receive_thread(self):
        """启动接收线程"""
        if self._receive_thread and self._receive_thread.is_alive():
            return
            
        self._stop_receive.clear()
        self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._receive_thread.start()
        self.logger.debug("CAN接收线程已启动")
    
    def _stop_receive_thread(self):
        """停止接收线程"""
        if self._receive_thread and self._receive_thread.is_alive():
            self._stop_receive.set()
            self._receive_thread.join(timeout=2.0)
            self.logger.debug("CAN接收线程已停止")
    
    def _receive_loop(self):
        """接收循环 (在独立线程中运行)"""
        while not self._stop_receive.is_set() and self.bus:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg is None:
                    continue
                
                # 转换为内部CANFrame格式
                frame = CANFrame(
                    arbitration_id=msg.arbitration_id,
                    data=bytes(msg.data),
                    is_extended=msg.is_extended_id
                )
                
                # 放入接收队列
                self._receive_queue.put(frame)
                
                # 调用回调函数
                for callback in self._message_callbacks:
                    try:
                        callback(frame)
                    except Exception as e:
                        self.logger.error(f"消息回调函数执行失败: {e}")
                
                self.logger.debug(f"接收CAN帧: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
                
            except Exception as e:
                if not self._stop_receive.is_set():
                    self.logger.error(f"CAN接收错误: {e}")
                    time.sleep(0.1)
    
    def flush_receive_queue(self):
        """清空接收队列"""
        while not self._receive_queue.empty():
            try:
                self._receive_queue.get_nowait()
            except Empty:
                break
    
    def get_statistics(self) -> dict:
        """获取通信统计信息"""
        stats = {
            'connected': self.is_connected,
            'interface': self.interface,
            'channel': self.channel,
            'bitrate': self.bitrate,
            'queue_size': self._receive_queue.qsize()
        }
        
        if self.bus and hasattr(self.bus, 'get_stats'):
            try:
                bus_stats = self.bus.get_stats()
                stats.update(bus_stats)
            except:
                pass
                
        return stats
    
    def __enter__(self):
        """上下文管理器支持"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        self.disconnect()


class MockCANHardware(CANHardware):
    """模拟CAN硬件 (用于测试)
    
    提供一个不需要真实硬件的CAN接口，方便开发和测试。
    """
    
    def __init__(self):
        super().__init__(interface='mock', channel='mock0')
        self._mock_responses = {}
    
    def connect(self) -> bool:
        """模拟连接"""
        self.is_connected = True
        self.logger.info("模拟CAN总线连接成功")
        return True
    
    def disconnect(self):
        """模拟断开"""
        self.is_connected = False
        self.logger.info("模拟CAN总线断开")
    
    def send_frame(self, frame: CANFrame, timeout: float = 1.0) -> bool:
        """模拟发送"""
        if not self.is_connected:
            return False
        
        self.logger.debug(f"模拟发送: ID=0x{frame.arbitration_id:03X}, Data={frame.data.hex().upper()}")
        
        # 检查是否有预设的响应
        response_key = (frame.arbitration_id, bytes(frame.data))
        if response_key in self._mock_responses:
            response_frame = self._mock_responses[response_key]
            # 延迟一点时间模拟真实响应
            threading.Timer(0.01, lambda: self._receive_queue.put(response_frame)).start()
        
        return True
    
    def set_mock_response(self, request_id: int, request_data: bytes, response_frame: CANFrame):
        """设置模拟响应"""
        self._mock_responses[(request_id, request_data)] = response_frame
