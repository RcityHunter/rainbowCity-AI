# 彩虹城 AI 系统 API 文档

## 目录

- [介绍](#介绍)
- [认证 API](#认证-api)
  - [用户注册](#用户注册)
  - [用户登录](#用户登录)
  - [获取用户资料](#获取用户资料)
  - [更新用户资料](#更新用户资料)
  - [修改密码](#修改密码)
- [聊天 API](#聊天-api)
  - [聊天对话](#聊天对话)
  - [聊天代理](#聊天代理)
  - [简单聊天](#简单聊天)
- [搜索 API](#搜索-api)
  - [执行搜索](#执行搜索)
  - [快速搜索](#快速搜索)
- [工具 API](#工具-api)
  - [AI-ID 生成器](#ai-id-生成器)
  - [频率编号生成器](#频率编号生成器)
  - [关系管理器](#关系管理器)
- [环境配置](#环境配置)

## 介绍

彩虹城 AI 系统提供了一套完整的 API，用于构建智能对话应用。本文档详细介绍了系统的各个 API 端点，包括认证、聊天、搜索和工具调用等功能。

所有 API 端点都以 `/api` 为前缀，例如 `/api/auth/login`。

## 认证 API

### 用户注册

**端点**：`POST /api/auth/register`

**描述**：注册新用户账号

**请求体**：
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "StrongPassword123",
  "display_name": "Display Name",
  "invite_code": "INV-ABCD1234" // 可选
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_12345",
    "email": "user@example.com",
    "username": "username",
    "display_name": "Display Name",
    "roles": ["user"],
    "vip_level": "basic"
  }
}
```

### 用户登录

**端点**：`POST /api/auth/login`

**描述**：用户登录并获取访问令牌

**请求体**：
```json
{
  "username": "user@example.com", // 使用邮箱作为用户名
  "password": "StrongPassword123"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_12345",
    "email": "user@example.com",
    "username": "username",
    "display_name": "Display Name",
    "roles": ["user"],
    "vip_level": "basic"
  }
}
```

### 获取用户资料

**端点**：`GET /api/auth/profile`

**描述**：获取当前登录用户的资料

**请求头**：
```
Authorization: Bearer {access_token}
```

**响应**：
```json
{
  "email": "user@example.com",
  "username": "username",
  "display_name": "Display Name",
  "created_at": "2023-01-01T00:00:00Z",
  "is_activated": true,
  "activation_status": "active",
  "roles": ["user"],
  "vip_level": "basic",
  "personal_invite_code": "INV-ABCD1234",
  "daily_chat_limit": 100,
  "weekly_invite_limit": 5,
  "ai_companions_limit": 3
}
```

### 更新用户资料

**端点**：`PUT /api/auth/profile`

**描述**：更新当前登录用户的资料

**请求头**：
```
Authorization: Bearer {access_token}
```

**请求体**：
```json
{
  "username": "new_username",
  "display_name": "New Display Name"
}
```

**响应**：
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "username": "new_username",
    "display_name": "New Display Name",
    "email": "user@example.com"
  }
}
```

### 修改密码

**端点**：`PUT /api/auth/password`

**描述**：修改当前登录用户的密码

**请求头**：
```
Authorization: Bearer {access_token}
```

**请求体**：
```json
{
  "current_password": "CurrentPassword123",
  "new_password": "NewStrongPassword123"
}
```

**响应**：
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

## 聊天 API

### 聊天对话

**端点**：`POST /api/chat`

**描述**：发送消息并获取 AI 回复，支持工具调用和多模态消息

**请求头**：
```
Authorization: Bearer {access_token} // 可选，匿名用户可不提供
```

**请求体**：
```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，请告诉我北京今天的天气",
      "type": "text"
    }
  ],
  "session_id": "session_12345", // 可选，不提供则自动生成
  "turn_id": "turn_12345" // 可选，不提供则自动生成
}
```

**响应**：
```json
{
  "success": true,
  "response": {
    "content": "根据最新的天气信息，北京今天的天气晴朗，气温在25°C到32°C之间，空气质量良好，适合户外活动。",
    "type": "text",
    "metadata": {
      "model": "gpt-3.5-turbo",
      "created": 1687654321,
      "session_id": "session_12345",
      "turn_id": "turn_12345"
    }
  },
  "tool_calls": [
    {
      "id": "call_12345",
      "name": "get_weather",
      "parameters": {
        "city": "北京",
        "date": "今天"
      }
    }
  ]
}
```

### 聊天代理

**端点**：`POST /api/chat/agent`

**描述**：使用 AI-Agent 处理聊天请求，集成记忆系统

**请求头**：
```
Authorization: Bearer {access_token} // 可选，匿名用户可不提供
```

**请求体**：
```json
{
  "messages": [
    {
      "role": "user",
      "content": "你能帮我生成一个 AI-ID 吗？",
      "type": "text"
    }
  ],
  "session_id": "session_12345", // 可选，不提供则自动生成
  "turn_id": "turn_12345" // 可选，不提供则自动生成
}
```

**响应**：
```json
{
  "success": true,
  "response": {
    "content": "我已经为您生成了一个 AI-ID：AI-7F3D2E1A。这是一个唯一的标识符，您可以用它来标识您的 AI 实体。",
    "type": "text",
    "metadata": {
      "model": "gpt-4o",
      "created": 1687654321,
      "session_id": "session_12345",
      "turn_id": "turn_12345"
    }
  },
  "tool_calls": [
    {
      "id": "call_12345",
      "name": "generate_ai_id",
      "parameters": {}
    }
  ]
}
```

### 简单聊天

**端点**：`POST /api/chat/simple`

**描述**：简单的聊天端点，直接返回 JSON 响应，支持工具调用和多模态消息

**请求体**：
```json
{
  "messages": [
    {
      "role": "user",
      "content": "生成一个频率编号",
      "type": "text"
    }
  ],
  "session_id": "session_12345", // 可选，不提供则自动生成
  "turn_id": "turn_12345" // 可选，不提供则自动生成
}
```

**响应**：
```json
{
  "response": {
    "content": "我已经为您生成了一个频率编号：F-PA-12345。这个编号可以用于标识特定的 AI 频率。",
    "type": "text",
    "metadata": {
      "model": "simple-model",
      "created": 1687654321,
      "session_id": "session_12345",
      "turn_id": "turn_12345"
    }
  },
  "tool_calls": [
    {
      "id": "call_12345",
      "name": "频率生成器",
      "parameters": {
        "ai_type": "A",
        "personality": "P"
      }
    }
  ]
}
```

## 搜索 API

### 执行搜索

**端点**：`POST /api/search`

**描述**：使用 Tavily 搜索引擎执行搜索

**请求体**：
```json
{
  "query": "北京最新天气预报",
  "search_depth": "basic", // basic 或 advanced
  "max_results": 10,
  "include_domains": ["weather.com", "accuweather.com"], // 可选
  "exclude_domains": ["example.com"], // 可选
  "include_answer": true,
  "include_raw_content": false,
  "include_images": false
}
```

**响应**：
```json
{
  "results": [
    {
      "title": "北京天气预报 - Weather.com",
      "url": "https://weather.com/zh-CN/weather/today/l/beijing",
      "content": "北京今日天气：晴朗，气温25°C-32°C，空气质量良好...",
      "score": 0.95,
      "published_date": "2023-06-25T10:00:00Z"
    },
    // 更多结果...
  ],
  "answer": "根据最新天气预报，北京今天晴朗，气温在25°C到32°C之间，空气质量良好，适合户外活动。未来三天将保持晴好天气，气温稳定。",
  "query": "北京最新天气预报"
}
```

### 快速搜索

**端点**：`GET /api/search/quick`

**描述**：使用默认参数执行快速搜索

**查询参数**：
- `query`：搜索查询（必需）

**示例**：`GET /api/search/quick?query=北京最新天气预报`

**响应**：
```json
{
  "results": [
    {
      "title": "北京天气预报 - Weather.com",
      "url": "https://weather.com/zh-CN/weather/today/l/beijing",
      "content": "北京今日天气：晴朗，气温25°C-32°C，空气质量良好...",
      "score": 0.95,
      "published_date": "2023-06-25T10:00:00Z"
    },
    // 更多结果...
  ],
  "answer": "根据最新天气预报，北京今天晴朗，气温在25°C到32°C之间，空气质量良好，适合户外活动。",
  "query": "北京最新天气预报"
}
```

## 工具 API

彩虹城 AI 系统提供了多种工具 API，可以通过聊天 API 中的工具调用功能使用。以下是主要的工具 API：

### AI-ID 生成器

**工具名称**：`generate_ai_id`

**描述**：生成唯一的 AI-ID 标识符

**参数**：
```json
{
  "name": "AI名称" // 可选
}
```

**返回值**：
```
AI-7F3D2E1A
```

### 频率编号生成器

**工具名称**：`generate_frequency`

**描述**：基于 AI-ID 生成频率编号

**参数**：
```json
{
  "ai_id": "AI-7F3D2E1A",
  "personality_type": "P", // 默认为 P
  "ai_type": "A" // 默认为 A
}
```

**返回值**：
```
F-PA-12345
```

### 关系管理器

**工具名称**：`relationship_manager`

**描述**：管理 AI 关系

**参数**：
```json
{
  "action": "create", // create, search, update
  "source_id": "AI-7F3D2E1A", // 源 AI-ID
  "target_id": "AI-9B8C7D6E", // 目标 AI-ID
  "relationship_type": "friend" // 关系类型
}
```

**返回值**：
```json
{
  "success": true,
  "relationship_id": "rel_12345",
  "source_id": "AI-7F3D2E1A",
  "target_id": "AI-9B8C7D6E",
  "relationship_type": "friend",
  "created_at": "2023-06-25T12:34:56Z"
}
```

## 环境配置

要使用彩虹城 AI 系统的 API，需要配置以下环境变量：

```env
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# Tavily API配置（用于实时搜索和天气查询）
TAVILY_API_KEY=your_tavily_api_key_here

# JWT密钥
JWT_SECRET_KEY=your_jwt_secret_key_here

# SurrealDB配置
SURREAL_URL=ws://localhost:8080
SURREAL_USER=root
SURREAL_PASS=123
SURREAL_NS=rainbow
SURREAL_DB=test
```

## 使用示例

### 使用 Python 发送聊天请求

```python
import requests
import json

# API 端点
url = "http://localhost:8000/api/chat"

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_access_token_here"  # 可选，匿名用户可不提供
}

# 请求体
data = {
    "messages": [
        {
            "role": "user",
            "content": "你好，请告诉我北京今天的天气",
            "type": "text"
        }
    ],
    "session_id": "session_12345"  # 可选，不提供则自动生成
}

# 发送请求
response = requests.post(url, headers=headers, data=json.dumps(data))

# 解析响应
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 使用 JavaScript 发送聊天请求

```javascript
async function sendChatRequest() {
  const url = 'http://localhost:8000/api/chat';
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your_access_token_here'  // 可选，匿名用户可不提供
  };
  
  const data = {
    messages: [
      {
        role: 'user',
        content: '你好，请告诉我北京今天的天气',
        type: 'text'
      }
    ],
    session_id: 'session_12345'  // 可选，不提供则自动生成
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    console.log(result);
  } catch (error) {
    console.error('Error:', error);
  }
}

sendChatRequest();
```