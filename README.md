# 电机控制SDK

一个完整的电机控制软件开发工具包(SDK)，基于CAN总线通信协议，采用模块化四层架构设计。

## 特性

- 🏗️ **模块化架构**: 四层设计，职责分离，易于维护和扩展
- 🔧 **简洁API**: 面向对象的高级接口，隐藏协议细节
- 🛡️ **安全保护**: 内置参数检查、心跳保护、错误处理
- 📟 **完整CLI**: 功能丰富的命令行工具，适合调试和测试
- 🔌 **硬件适配**: 支持多种CAN适配器，包含模拟硬件用于测试
- 📊 **实时监控**: 支持状态回调和实时数据监控

## 架构设计

```
┌─────────────────────────────────────┐
│        用户交互层 (CLI Tool)         │
│         cli_tool.py                │
├─────────────────────────────────────┤
│      电机控制API层 (Motor API)        │
│         motor_api.py               │
├─────────────────────────────────────┤
│    协议编码/解码层 (Protocol Layer)    │
│       protocol_layer.py            │
├─────────────────────────────────────┤
│     硬件通信层 (Hardware Layer)      │
│       hardware_layer.py            │
└─────────────────────────────────────┘
```

### 层次说明

1. **硬件通信层** - CAN总线硬件接口，支持多种适配器
2. **协议编码/解码层** - CAN报文格式处理，位操作和数据转换
3. **电机控制API层** - 高级电机控制接口，安全保护和状态管理
4. **用户交互层** - 命令行工具，提供完整的用户界面

## 安装要求

- Python 3.7+
- python-can库 (用于CAN通信)
- colorama库 (用于CLI彩色输出，可选)

```bash
pip install -r requirements.txt
```

## 快速开始

### 基本使用

```python
from encos_sdk import CANHardware, Motor

# 初始化CAN硬件
can_hw = CANHardware(interface='socketcan', channel='can0', bitrate=1000000)
can_hw.connect()

# 创建电机实例
motor = Motor(motor_id=1, can_hardware=can_hw)

# 基本操作
motor.set_zero_point()          # 设置零点
motor.set_position(90.0)        # 设置位置到90度
status = motor.get_status()     # 获取状态反馈

print(f"当前位置: {status.position:.2f}度")
print(f"当前速度: {status.velocity:.2f}RPM")

# 清理资源
can_hw.disconnect()
```

### 多电机控制

```python
from encos_sdk import CANHardware, MotorManager

with CANHardware(interface='socketcan', channel='can0') as can_hw:
    manager = MotorManager(can_hw)
    
    # 扫描总线上的电机
    motor_ids = manager.scan_motors()
    print(f"检测到电机: {motor_ids}")
    
    # 添加电机并控制
    for motor_id in motor_ids:
        motor = manager.add_motor(motor_id)
        motor.set_position(45.0 + motor_id * 30.0)  # 不同位置
    
    # 获取所有状态
    all_status = manager.get_all_status()
    for motor_id, status in all_status.items():
        if status:
            print(f"电机{motor_id}: {status.position:.2f}度")
```

### 状态监控

```python
# 添加状态回调
def on_status_update(status):
    print(f"位置: {status.position:.2f}度, 速度: {status.velocity:.2f}RPM")

def on_error(error_code):
    print(f"电机错误: {error_code}")

motor.add_status_callback("monitor", on_status_update)
motor.add_error_callback("error_handler", on_error)

# 开始运动
motor.set_position(180.0)
```

## CLI工具使用

SDK提供了功能完整的命令行工具，适合硬件调试和自动化测试。

### 基本命令

```bash
# 扫描总线上的电机
python cli_tool.py scan

# 设置电机1的零点
python cli_tool.py zero 1

# 位置控制: 电机1转到90度，速度限制100RPM，电流限制3A
python cli_tool.py pos 1 90 100 3.0

# 速度控制: 电机1转速50RPM，电流限制2A
python cli_tool.py vel 1 50 2.0

# 获取电机1状态
python cli_tool.py status 1

# 实时监控电机1状态
python cli_tool.py monitor 1 --interval 0.1
```

### 高级控制

```bash
# 使用力位混控模式
python cli_tool.py pos 1 90 100 3.0 --mode force

# 获取不同类型的反馈
python cli_tool.py status 1 --type 2  # Type2: 位置、速度、电流

# 指定CAN接口
python cli_tool.py --interface pcan --channel PCAN_USBBUS1 scan

# 详细输出
python cli_tool.py -v monitor 1
```

## 安全注意事项

⚠️ **重要安全提醒**:

- **固定电机**: 测试前务必将电机固定牢固
- **避免危险模式**: 切勿在未固定情况下测试电流/力矩模式
- **心跳保护**: 系统有500ms心跳保护，连续控制时注意指令间隔
- **参数限制**: 设置合理的位置、速度、电流安全限制
- **应急停止**: 随时准备切断电源

## API参考

### 主要类

- **`CANHardware`**: CAN硬件接口
- **`Motor`**: 单电机控制
- **`MotorManager`**: 多电机管理
- **`ProtocolEncoder/Decoder`**: 协议编码解码
- **`MotorStatus`**: 电机状态数据

### 控制模式

- **伺服位置模式**: 精确位置控制，适合定位应用
- **力位混控模式**: 柔顺控制，可设置刚度和阻尼
- **伺服速度模式**: 恒速控制，适合连续运动
- **电流控制模式**: 直接电流控制，适合力矩应用

### 反馈类型

- **Type 1**: 位置、速度、力矩反馈
- **Type 2**: 位置、速度、电流反馈
- **Type 3**: 位置、速度反馈 (高精度)
- **Type 4**: 电机状态反馈 (温度、电压等)
- **Type 5**: 错误信息反馈

## 故障排除

### 常见问题

1. **CAN硬件连接失败**
   - 检查CAN适配器驱动是否正确安装
   - 确认CAN接口名称 (如socketcan的'can0')
   - 检查CAN总线波特率设置 (默认1Mbps)

2. **电机无响应**
   - 确认电机ID设置正确
   - 检查CAN总线连接和终端电阻
   - 使用`scan`命令检测电机

3. **指令发送失败**
   - 检查心跳超时设置
   - 确认指令参数在合法范围内
   - 查看详细日志输出

4. **性能问题**
   - 减少监控频率
   - 使用合适的反馈类型
   - 避免频繁的状态查询

### 调试技巧

```bash
# 开启详细日志
python cli_tool.py -v monitor 1

# 检查CAN总线流量
candump can0

# 测试CAN硬件
cansend can0 123#DEADBEEF
```

## 许可证

本项目遵循MIT许可证。详情请参阅LICENSE文件。

## 贡献

欢迎提交问题报告、功能请求和代码贡献。请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 技术支持: [Email]

---

**版本**: 1.0.0  
**作者**: Dyna Team  
**更新时间**: 2025年8月
