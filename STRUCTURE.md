# 项目结构说明

## 目录结构

```
encos_sdk/
├── __init__.py              # 包初始化文件，导出主要API
├── data_types.py            # 数据类型定义 (MotorStatus, ErrorCode等)
├── hardware_layer.py        # 硬件通信层 (CANHardware, MockCANHardware)
├── protocol_layer.py        # 协议编码/解码层 (ProtocolEncoder, ProtocolDecoder)  
├── motor_api.py             # 电机控制API层 (Motor, MotorManager)
├── cli_tool.py              # 完整CLI工具 (需要python-can)
├── demo_cli.py              # 演示CLI工具 (无依赖)
├── examples.py              # 使用示例代码
├── test_sdk.py              # 完整功能测试 (需要python-can)
├── test_basic.py            # 基础功能测试 (无依赖)
├── requirements.txt         # 依赖列表
├── setup.py                 # 包安装脚本
├── Makefile                 # 自动化任务
├── README.md                # 详细文档
└── STRUCTURE.md             # 本文件
```

## 核心模块说明

### 1. data_types.py
- **MotorStatus**: 电机状态数据结构
- **ErrorCode**: 错误代码枚举
- **FeedbackType**: 反馈类型枚举
- **CANFrame**: CAN数据帧结构
- **ProtocolConstants**: 协议常量定义
- 工具函数: float_to_bytes, bytes_to_float等

### 2. hardware_layer.py
- **CANHardware**: 真实CAN硬件接口类
  - 支持多种CAN适配器 (socketcan, pcan, vector等)
  - 异步接收机制
  - 消息回调支持
- **MockCANHardware**: 模拟硬件类，用于测试

### 3. protocol_layer.py
- **ProtocolEncoder**: 协议编码器
  - encode_query_id(): 查询电机ID
  - encode_set_zero_point(): 设置零点
  - encode_servo_position_command(): 伺服位置模式
  - encode_force_position_command(): 力位混控模式
  - encode_servo_speed_command(): 伺服速度模式
- **ProtocolDecoder**: 协议解码器
  - decode_feedback(): 解码反馈报文
  - 支持Type1-5所有反馈类型

### 4. motor_api.py
- **Motor**: 单电机控制类
  - set_position(): 位置控制
  - set_velocity(): 速度控制
  - get_status(): 状态获取
  - 安全保护和错误处理
  - 状态回调机制
- **MotorManager**: 多电机管理类
  - scan_motors(): 扫描电机
  - 集中控制多个电机

### 5. cli_tool.py
完整的命令行工具，支持:
- scan: 扫描电机
- zero: 设置零点
- pos: 位置控制
- vel: 速度控制
- status: 状态查询
- monitor: 实时监控
- config: 配置管理

## 使用流程

### 无硬件测试
```bash
# 1. 基础功能测试
python test_basic.py

# 2. CLI演示
python demo_cli.py --help
python demo_cli.py scan
python demo_cli.py pos 1 90
```

### 带硬件使用
```bash
# 1. 安装依赖
pip install python-can colorama

# 2. 完整测试
python test_sdk.py

# 3. 真实CLI使用
python cli_tool.py scan
python cli_tool.py zero 1
python cli_tool.py pos 1 90 100 3.0
```

### 编程使用
```python
from encos_sdk import CANHardware, Motor

# 基础使用
can_hw = CANHardware('socketcan', 'can0')
can_hw.connect()
motor = Motor(1, can_hw)
motor.set_position(90.0)
status = motor.get_status()
```

## 设计特点

1. **四层架构**: 清晰的职责分离
2. **模块化设计**: 每个模块功能独立
3. **安全保护**: 参数检查、错误处理、心跳保护
4. **易于扩展**: 支持新的控制模式和反馈类型
5. **测试友好**: 提供模拟硬件和无依赖测试
6. **文档完整**: 详细的API文档和使用示例

## 开发指南

1. **添加新指令**: 在protocol_layer.py中添加编码/解码函数
2. **扩展电机功能**: 在motor_api.py的Motor类中添加方法
3. **增加CLI命令**: 在cli_tool.py中添加新的子命令
4. **适配新硬件**: 继承CANHardware类或实现新的接口

这个SDK提供了完整的电机控制解决方案，从底层CAN通信到高级API，从命令行工具到编程接口，满足不同层次的使用需求。
