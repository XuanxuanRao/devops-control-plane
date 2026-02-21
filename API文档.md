# DevOps 控制平面后端接口文档

## 1. 整体功能介绍

DevOps 控制平面是一个集中式的服务器管理和命令下发系统，主要功能包括：

- **服务器管理**：添加、查看服务器信息，包括主机名、IP、分组、状态、心跳时间、CPU和内存使用率等
- **命令下发**：向指定服务器、服务器组或所有服务器下发命令，并获取执行结果
- **任务管理**：查看任务执行状态和详细结果
- **公钥管理**：为不同客户端（服务器）管理RSA公钥，用于消息签名验证
- **健康检查**：提供系统健康状态检查接口

系统采用 FastAPI 框架开发，使用 MySQL 数据库存储数据，RabbitMQ 作为消息队列进行命令下发，支持 RSA 数字签名进行消息安全验证。

## 2. API 接口详情

### 2.1 健康检查

**接口路径**：`GET /api/health`

**功能**：检查系统健康状态

**响应**：
```json
{
  "status": "ok"
}
```

### 2.2 服务器管理

#### 2.2.1 获取服务器列表

**接口路径**：`GET /api/servers`

**功能**：获取所有服务器的详细信息

**响应**：
```json
[
  {
    "hostname": "server1",
    "ip": "192.168.1.100",
    "group": "web",
    "status": "online",
    "last_heartbeat": "2024-01-01T12:00:00Z",
    "cpu_usage": 15.5,
    "memory_usage": 60.2
  }
]
```

#### 2.2.2 添加服务器

**接口路径**：`POST /api/servers`

**功能**：添加新的服务器

**请求体**：
```json
{
  "hostname": "server1",
  "ip": "192.168.1.100",
  "group": "web"
}
```

**响应**：
```json
{
  "hostname": "server1",
  "ip": "192.168.1.100",
  "group": "web",
  "status": "offline",
  "last_heartbeat": null,
  "cpu_usage": null,
  "memory_usage": null
}
```

**错误码**：
- 409 Conflict：主机名已存在

### 2.3 任务管理

#### 2.3.1 获取任务列表

**接口路径**：`GET /api/tasks`

**功能**：获取所有任务的详细信息

**响应**：
```json
[
  {
    "task_id": "abc123",
    "target_type": "all",
    "target": null,
    "command": "ls -la",
    "timeout": 30,
    "user": "root",
    "status": "sent",
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

### 2.4 命令下发

**接口路径**：`POST /api/commands`

**功能**：向指定目标下发命令

**请求体**：
```json
{
  "target_type": "all",
  "target": null,
  "command": "ls -la",
  "timeout": 30,
  "user": "root"
}
```

**参数说明**：
- `target_type`：目标类型，可选值为 `node`（单个节点）、`group`（节点组）、`all`（所有节点）
- `target`：目标值，当 `target_type` 为 `node` 或 `group` 时必填
- `command`：要执行的命令
- `timeout`：命令执行超时时间（秒），默认30秒
- `user`：执行命令的用户

**响应**：
```json
{
  "task_id": "abc123",
  "target_type": "all",
  "target": null,
  "command": "ls -la",
  "timeout": 30,
  "user": "root",
  "status": "sent",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**错误码**：
- 400 Bad Request：目标类型无效或目标值缺失

### 2.5 任务结果查询

**接口路径**：`GET /api/tasks/{task_id}/results`

**功能**：获取指定任务的执行结果

**响应**：
```json
[
  {
    "task_id": "abc123",
    "exit_code": 0,
    "stdout": "total 20\ndrwxr-xr-x  5 user  group  160 Jan  1 12:00 .\ndrwxr-xr-x  3 user  group   96 Dec 31 23:59 ..\n",
    "stderr": "",
    "timestamp": "2024-01-01T12:00:01Z"
  }
]
```

### 2.6 公钥管理

#### 2.6.1 获取公钥列表

**接口路径**：`GET /api/client-keys`

**功能**：获取所有客户端公钥信息

**响应**：
```json
[
  {
    "hostname": "server1",
    "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

#### 2.6.2 获取指定客户端公钥

**接口路径**：`GET /api/client-keys/{hostname}`

**功能**：获取指定客户端（服务器）的公钥信息

**响应**：
```json
{
  "hostname": "server1",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**错误码**：
- 404 Not Found：公钥不存在

#### 2.6.3 上传/更新客户端公钥

**接口路径**：`PUT /api/client-keys/{hostname}`

**功能**：为指定客户端（服务器）上传或更新RSA公钥

**请求体**：
```json
{
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"
}
```

**响应**：
```json
{
  "hostname": "server1",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**错误码**：
- 400 Bad Request：无效的公钥格式

## 3. 数据模型

### 3.1 Server 模型

| 字段名 | 类型 | 描述 |
|-------|------|------|
| hostname | string | 服务器主机名，唯一标识 |
| ip | string | 服务器IP地址 |
| group | string | 服务器分组 |
| status | string | 服务器状态 |
| last_heartbeat | datetime | 最后心跳时间 |
| cpu_usage | float | CPU使用率 |
| memory_usage | float | 内存使用率 |

### 3.2 Task 模型

| 字段名 | 类型 | 描述 |
|-------|------|------|
| task_id | string | 任务ID，唯一标识 |
| target_type | string | 目标类型（node/group/all） |
| target | string | 目标值 |
| command | string | 执行的命令 |
| timeout | int | 超时时间（秒） |
| user | string | 执行用户 |
| status | string | 任务状态 |
| created_at | datetime | 创建时间 |

### 3.3 TaskResult 模型

| 字段名 | 类型 | 描述 |
|-------|------|------|
| task_id | string | 任务ID |
| exit_code | int | 退出码 |
| stdout | string | 标准输出 |
| stderr | string | 标准错误 |
| timestamp | datetime | 执行时间 |

### 3.4 ClientPublicKey 模型

| 字段名 | 类型 | 描述 |
|-------|------|------|
| hostname | string | 客户端主机名，唯一标识 |
| public_key_pem | string | RSA公钥PEM格式 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 4. 错误处理

系统使用 HTTP 状态码表示错误类型：

| 状态码 | 描述 | 示例 |
|-------|------|------|
| 400 | 请求参数错误 | 无效的目标类型、目标值缺失、无效的公钥格式 |
| 404 | 资源不存在 | 公钥不存在 |
| 409 | 资源冲突 | 主机名已存在 |

错误响应格式：
```json
{
  "detail": "错误描述"
}
```
