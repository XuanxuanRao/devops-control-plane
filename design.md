# 技术选型
后端框架采用 fast api，数据库采用 mysql，消息队列采用 rabbitmq。前端尽可能简单，采用 html、css、js 等原生技术，不采用任何前端框架。全部在一个项目中实现，前端与后端通过 api 交互。

# 需求分析
实现一个简单的 devops 控制平面，用户可以在控制面板上查看当前所有的服务器状态，并在服务器上执行指令。

通过消息队列与服务器进行通信。下面是相关的定义
根据当前项目，我已经整理出了项目中用到的消息队列及其作用：

## 1. 命令消息队列系统

### 交换机
- **名称**: `sys_cmd_exchange`
- **类型**: `topic`
- **作用**: 接收和分发命令消息到各个 Agent

### 路由键
- **单机指令**: `cmd.node.{hostname}` - 发送给特定主机的命令
- **广播指令**: `cmd.all` - 发送给所有 Agent 的命令
- **分组指令**: `cmd.group.{group}` - 发送给特定分组的 Agent 的命令

### 队列
- **名称**: `cmd.node.{hostname}` (每个 Agent 一个)
- **作用**: 每个 Agent 的私有队列，接收发送给它的命令
- **特性**: 专属队列 (exclusive=true)，当 Agent 离线后自动删除

### 消息协议
- **格式**: JSON 字符串
- **内容**: 包含指令、参数、超时时间等信息
- **示例**:
  ```json
  {
    "task_id": "123456",
    "command": "ls -l",
    "timeout": 30,
    "user": "root",
    "timestamp": 1694582400,
    "sign": "base64_encoded_signature"
  }
  ```

## 2. 结果消息队列系统

### 交换机
- **名称**: `sys_result_exchange`
- **类型**: `topic`
- **作用**: 接收和分发命令执行结果

### 路由键
- **结果回传**: `result.node.{hostname}` - 特定主机的命令执行结果

### 队列
- **名称**: `cmd.result` (由控制平面创建)
- **作用**: 接收所有 Agent 的命令执行结果
- **绑定**: 控制平面应该将此队列绑定到 `result.#` 路由键，以接收所有结果

### 消息协议
- **格式**: JSON 字符串
- **内容**: 包含 Agent 状态、心跳时间等信息
- **示例**:
  ```json
  {
    "task_id": "123456",
    "exit_code": 0,
    "stdout": "hello",
    "stderr": "",
    "timestamp": 1694582400,
    "signature": "base64_encoded_signature"
  }
  ```

## 3. 心跳消息队列系统

### 交换机
- **名称**: `sys_monitor_exchange`
- **类型**: `topic`

### 路由键
- **心跳消息**: `heartbeat` - Agent 发送的心跳消息

### 队列
- **名称**: 由控制平面创建 (例如 `monitor.heartbeat`)
- **作用**: 接收所有 Agent 的心跳消息
- **绑定**: 控制平面应该将此队列绑定到 `heartbeat` 路由键，以接收所有心跳消息

### 消息协议
- **格式**: JSON 字符串
- **内容**: 包含 Agent 状态、心跳时间等信息
- **示例**:
  ```json
  {
    "hostname": "agent-1",
    "status": "online",
    "timestamp": 1694582400,
    "cpu_usage": 0.5,
    "memory_usage": 0.7,
    "signature": "base64_encoded_signature"
  }
  ```

## 消息流

1. **命令下发**: 控制平面 → `sys_cmd_exchange` → Agent 私有队列 → Agent 执行命令
2. **结果回传**: Agent → `sys_result_exchange` → `cmd.result` 队列 → 控制平面接收结果
3. **心跳上报**: Agent → `sys_monitor_exchange` → 心跳队列 → 控制平面监控 Agent 状态

## 队列特性

- **专属队列**: 每个 Agent 的命令队列都是专属的，确保消息安全和隔离
- **自动删除**: 当 Agent 离线时，其专属队列会自动删除，避免消息堆积
- **多路由绑定**: 每个 Agent 的队列绑定到多个路由键，实现单机、广播和分组指令的支持
- **结果集中管理**: 所有执行结果发送到同一个交换机，控制平面可以集中接收和处理


# 系统架构
## 架构概览
系统由控制平面、消息队列、Agent、数据库四部分组成。控制平面提供 Web UI 与 API，负责编排命令、收集结果与心跳。消息队列承担命令分发、结果回传与心跳上报。Agent 部署在各服务器上，执行命令并上报状态。数据库保存主机信息、任务记录与结果。

## 组件职责
- 控制平面（Web UI + API）：展示服务器列表与状态，创建并下发命令，聚合执行结果与心跳，提供审计与查询接口
- 消息队列（RabbitMQ）：承载命令、结果、心跳三类消息流，支持单机、分组与广播
- Agent：订阅命令队列并执行任务，推送执行结果与心跳
- 数据库（MySQL）：持久化服务器资产、任务、执行结果、心跳快照

## 逻辑架构
1. Web UI 调用 API 创建任务
2. API 生成任务记录并发布命令到 sys_cmd_exchange
3. Agent 订阅自身队列并执行命令
4. Agent 将执行结果发布到 sys_result_exchange
5. 控制平面消费 cmd.result 队列并写入数据库
6. Agent 定期发布心跳到 sys_monitor_exchange
7. 控制平面消费心跳并更新服务器状态

## 部署架构
控制平面部署为单体应用，内部包含 API 与静态页面。RabbitMQ 与 MySQL 可独立部署为高可用服务。Agent 部署在各目标服务器上。

## 数据流与消息流
- 命令下发流：Web UI → API → sys_cmd_exchange → Agent 私有队列 → Agent
- 结果回传流：Agent → sys_result_exchange → cmd.result → 控制平面 → MySQL
- 心跳上报流：Agent → sys_monitor_exchange → 心跳队列 → 控制平面 → MySQL

## 可靠性与安全
- 消息可靠性：命令与结果使用持久化消息，消费者开启手动 ack
- 幂等设计：task_id 作为幂等键，重复消息不影响最终结果
- 访问控制：API 层校验用户身份与权限
