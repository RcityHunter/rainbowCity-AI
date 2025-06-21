# Rainbow City - AI共生社区 

![Rainbow City Logo](frontend/public/logo.png)

## 目录

- [项目概述](#项目概述)
- [主要功能](#主要功能)
  - [彩虹城AI聊天](#彩虹城ai聊天)
  - [一体七翼生成器 (AI-ID)](#一体七翼生成器-ai-id)
  - [频率编号生成器](#频率编号生成器)
  - [关系管理](#关系管理)
- [技术栈](#技术栈)
- [安装指南](#安装指南)
  - [前端部署](#前端部署)
  - [后端部署](#后端部署)
  - [环境变量配置](#环境变量配置)
- [使用指南](#使用指南)
- [特色亮点](#特色亮点)
- [API 调用指南](#api-调用指南)
  - [认证API](#认证api)
  - [AI聊天API](#ai聊天api)
  - [AI-ID和频率编号API](#ai-id和频率编号api)
  - [关系管理API](#关系管理api)
  - [对话管理API](#对话管理api)
  - [文件和图片API](#文件和图片api)
- [Agent系统架构](#agent系统架构)
- [贡献指南](#贡献指南)
- [开发环境配置问题解决](#开发环境配置问题解决)
- [许可证](#许可证)
- [联系方式](#联系方式)

## 项目概述

Rainbow City（彩虹城）是一个创新的AI交互平台，集成了一体七翼系统、AI聊天和关系管理功能。该系统采用现代化的深色主题设计，提供直观的用户界面和流畅的交互体验，旨在创建一个全面的AI共生社区生态系统。

核心技术包括基于大语言模型的智能对话系统，支持多模态输入（文本、图片、文档等），以及工具调用能力，可实现天气查询、AI-ID生成、频率编号生成等功能。

## 主要功能

### 彩虹城AI聊天
- 与先进的AI助手进行自然对话
- 支持文本、图片和音频等多模态输入
- 悬停式聊天历史侧边栏，提供便捷的会话管理
- 现代化的上传文件界面，支持多种文件类型
- 科技感十足的UI设计，提供沉浸式体验

### 一体七翼生成器 (AI-ID)
- 生成唯一的一体七翼标识符
- 可视化展示生成的标识符
- 一键复制功能，方便用户使用
- 详细的标识符信息展示

### 频率编号生成器
- 基于一体七翼标识符生成频率编号
- 自定义AI价值观参数（关怀、真实、自主、协作、进化、创新、责任）
- 选择不同的性格类型和AI类型
- 详细的频率编号组成分析

### 关系管理
- 可视化展示彩虹城AI与用户之间的关系网络
- 基于力导向图的动态关系展示
- 关系强度和状态的直观表示
- 详细的节点信息查看

## 技术栈

### 前端
- React.js
- CSS3 (包括变量、动画和响应式设计)
- 模块化CSS组件系统
- SVG图形和动画
- 数据可视化组件
- 玻璃态设计 (Glassmorphism)
- 多模态交互界面

### 后端
- Python + FastAPI
- RESTful API设计
- OAuth2 认证机制
- 第三方社交登录（Google、GitHub）
- Pydantic 数据验证
- 数据持久化存储
- 大语言模型集成（OpenAI API）
- 多模态输入处理（文本、图片、文档等）
- 模块化Agent系统架构
- 工具调用框架

## 安装指南

### 前提条件
- Node.js (v14.0.0或更高版本)
- npm (v6.0.0或更高版本)
- Python (v3.8或更高版本)
- pip (最新版本)

### 前端部署

1. 克隆仓库
   ```bash
   git clone https://github.com/RcityHunter/rainbowCity-AI.git
   cd rainbowCity-AI
   ```

2. 安装前端依赖
   ```bash
   cd frontend
   npm install
   ```

3. 配置前端环境变量
   在`frontend`目录中创建`.env`文件，添加以下内容：
   ```
   HOST=localhost
   PORT=3000
   WDS_SOCKET_HOST=localhost
   DANGEROUSLY_DISABLE_HOST_CHECK=true
   REACT_APP_API_URL=http://localhost:5001/api
   ```

4. 启动前端开发服务器
   ```bash
   npm start
   ```
   前端将在 http://localhost:3000 运行

### 后端部署

1. 创建并激活虚拟环境（推荐）
   ```bash
   # 进入后端目录
   cd backend
   
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境（Windows）
   venv\Scripts\activate
   
   # 激活虚拟环境（macOS/Linux）
   source venv/bin/activate
   ```

2. 安装后端依赖
   ```bash
   # 确保在虚拟环境中
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. 配置后端环境变量
   在`backend`目录中创建`.env`文件，添加必要的环境变量

4. 启动后端服务
   ```bash
   # 开发模式
   python run.py
   
   # 生产模式（使用gunicorn，仅适用于Linux/macOS）
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.app:app --bind 0.0.0.0:5001
   ```
   后端API将在 http://localhost:5001/api 运行

### 环境变量配置

#### 后端环境变量（.env文件）
```
# SurrealDB配置
SURREAL_URL=ws://localhost:8080
SURREAL_USER=root
SURREAL_PASS=123
SURREAL_NS=rainbow
SURREAL_DB=test

# 服务器配置
PORT=5001

# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key

# JWT密钥
JWT_SECRET_KEY=your_jwt_secret_key_here

# Google OAuth配置
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/oauth/google/callback

# GitHub OAuth配置
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:3000/oauth/github/callback
```

#### 获取OAuth凭证

1. **Google OAuth凭证**
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建一个新项目
   - 在“凭证”部分创建 OAuth 2.0 客户端 ID
   - 添加重定向URI：`http://localhost:3000/oauth/google/callback`
   - 复制客户端 ID 和客户端密钥到你的`.env`文件

2. **GitHub OAuth凭证**
   - 访问 [GitHub Developer Settings](https://github.com/settings/developers)
   - 点击“New OAuth App”
   - 填写应用程序信息
   - 添加回调URL：`http://localhost:3000/oauth/github/callback`
   - 创建应用程序后，复制客户端 ID 和生成客户端密钥
   - 将这些值添加到你的`.env`文件中

### 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:5001/api

## 使用指南

### 彩虹城AI聊天
1. 点击首页上的“开始聊天”按钮
2. 在输入框中输入文字与 AI 对话
3. 悬停在左侧可显示聊天历史侧边栏
4. 点击左下角的回形针图标可显示上传选项：
   - 图片上传：点击图片图标上传图片
   - 音频上传：点击音频图标上传音频文件
   - 文档上传：点击文档图标上传其他类型文件
5. 点击“发送”按钮或按回车键发送消息
6. 使用工具能力：
   - 天气查询：输入“查询北京天气”等请求
   - AI-ID生成：输入“生成一个AI-ID”
   - 频率编号生成：输入“根据AI-ID生成频率编号”
   - 图片分析：上传图片后系统自动分析
   - 文档处理：上传文档后可进行分析、摘要等操作

### 一体七翼生成器
1. 点击“了解更多”按钮进入一体七翼生成器
2. 点击“生成 AI-ID”按钮
3. 系统将生成一个唯一的标识符
4. 点击标识符可复制到剪贴板
5. 查看详细信息和统计数据

### 频率编号生成器
1. 首先生成一个一体七翼标识符
2. 设置唤醒者ID（默认为user123）
3. 调整AI价值观滑块（7个维度）
4. 选择性格类型和AI类型
5. 点击“生成频率编号”按钮
6. 查看生成的频率编号和详细信息

### 关系管理
1. 查看彩虹城AI与用户之间的可视化关系网络图
2. 点击节点可查看详细信息
3. 观察不同颜色和线条粗细代表的关系状态和强度

## 特色亮点

- **多模态交互**：支持文本、图片和音频等多种内容类型，使交流更加自然和丰富
- **玻璃态设计**：采用现代的玻璃态设计，创造半透明模糊效果，提升界面美观度
- **悬停式侧边栏**：创新的悬停显示聊天历史侧边栏，节省界面空间的同时提供便捷访问
- **现代深色主题**：采用符合当代设计趋势的深色主题，减少眼睛疲劳
- **社交快速登录**：支持Google和GitHub第三方登录，简化用户注册和登录流程
- **科技感图标**：精心设计的科技感图标，增强用户体验和界面美观度
- **响应式设计**：完美适配各种屏幕尺寸，从手机到桌面设备
- **流畅动画**：精心设计的过渡和动画效果，提升用户体验
- **可访问性**：支持减少动画选项，照顾有特殊需求的用户
- **直观交互**：简洁明了的用户界面，降低学习成本
- **模块化Agent系统**：基于组件化设计的AI对话管理系统，易于扩展和维护
- **工具调用能力**：支持动态注册和调用外部工具，实现功能扩展
- **完整的对话上下文管理**：支持多轮对话和上下文保持
- **详细的事件日志**：记录用户输入、LLM调用、工具调用等完整交互过程

## API 调用指南

彩虹城AI系统提供了一套完整的RESTful API，基于FastAPI实现。所有API路由都以`/api`为前缀，采用OAuth2 Bearer Token认证机制。以下所有示例假设后端服务器运行在 `http://localhost:5001`。

### 认证API

#### 用户注册
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "StrongPassword123",
  "display_name": "Display Name",
  "invite_code": "INV-XXXXXXXX" (可选)
}
```

**响应：**
```json
{
  "status": "success",
  "message": "注册成功",
  "user": {
    "id": "user_123456",
    "email": "user@example.com",
    "username": "username",
    "display_name": "Display Name"
  }
}
```

#### 用户登录
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=StrongPassword123
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_123456",
    "email": "user@example.com",
    "username": "username",
    "display_name": "Display Name"
  }
}
```

#### OAuth社交登录

##### 获取Google授权URL
```http
GET /api/oauth/google/auth
```

**响应：**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=your_client_id&redirect_uri=http://localhost:3000/oauth/google/callback&response_type=code&scope=email profile&access_type=offline&prompt=consent"
}
```

##### 获取GitHub授权URL
```http
GET /api/oauth/github/auth
```

**响应：**
```json
{
  "auth_url": "https://github.com/login/oauth/authorize?client_id=your_client_id&redirect_uri=http://localhost:3000/oauth/github/callback&scope=user:email"
}
```

##### 处理Google OAuth回调
```http
POST /api/oauth/google/callback
Content-Type: application/json

{
  "code": "4/0AeaYSHDkLTwYjhGXxLAZ8YNnYJVd..."
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_123456",
    "email": "user@example.com",
    "username": "google_12345678",
    "display_name": "Google User",
    "oauth_provider": "google"
  }
}
```

##### 处理GitHub OAuth回调
```http
POST /api/oauth/github/callback
Content-Type: application/json

{
  "code": "a1b2c3d4e5f6g7h8i9j0..."
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_789012",
    "email": "user@example.com",
    "username": "github_username",
    "display_name": "GitHub User",
    "oauth_provider": "github"
  }
}
```

#### 刷新访问令牌
```http
POST /api/auth/refresh
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 获取当前用户信息
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": "user_123456",
  "email": "user@example.com",
  "username": "username",
  "display_name": "Display Name",
  "created_at": "2025-01-15T08:30:00Z",
  "is_active": true
}
```

### AI聊天API

#### 发送聊天消息
```http
POST /api/chat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "session_id": "session_uuid",
  "turn_id": "turn_uuid",
  "messages": [
    {"role": "user", "content": "你好，请介绍一下彩虹城"}
  ],
  "user_id": "user_123456",
  "ai_id": "ai_rainbow_city"
}
```

**响应：**
```json
{
  "id": "msg_789012",
  "role": "assistant",
  "content": "你好！我是彩虹城 AI助手，彩虹城是一个创新的AI交互平台，集成了一体七翼系统、AI聊天和关系管理功能...",
  "session_id": "session_uuid",
  "turn_id": "turn_uuid",
  "timestamp": "2025-06-21T03:45:12Z"
}
```

#### 创建新的聊天会话
```http
POST /api/chat/sessions
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "user_123456",
  "ai_id": "ai_rainbow_city",
  "title": "新的聊天会话"
}
```

**响应：**
```json
{
  "id": "session_uuid",
  "user_id": "user_123456",
  "ai_id": "ai_rainbow_city",
  "title": "新的聊天会话",
  "created_at": "2025-06-21T03:45:00Z",
  "updated_at": "2025-06-21T03:45:00Z"
}
```

#### 带文件的聊天请求
```http
POST /api/chat/agent/with_file
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

user_input: "这张图片是什么？"
session_id: "session_uuid"
user_id: "user_123456"
ai_id: "ai_rainbow_city"
image: [二进制图片文件]
```

**响应：**
```json
{
  "id": "msg_789013",
  "role": "assistant",
  "content": "这张图片显示的是一座城市的天际线，有多座高楼和现代化建筑...",
  "session_id": "session_uuid",
  "turn_id": "turn_uuid",
  "timestamp": "2025-06-21T03:46:30Z"
}
```

#### 获取聊天历史
```http
GET /api/chat/history?session_id=session_uuid
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "messages": [
    {
      "id": "msg_789010",
      "role": "user",
      "content": "你好，请介绍一下彩虹城",
      "session_id": "session_uuid",
      "timestamp": "2025-06-21T03:45:00Z"
    },
    {
      "id": "msg_789012",
      "role": "assistant",
      "content": "你好！我是彩虹城 AI助手...",
      "session_id": "session_uuid",
      "timestamp": "2025-06-21T03:45:12Z"
    }
  ],
  "session_id": "session_uuid",
  "total_messages": 2
}
```

### AI-ID和频率编号API

#### 生成AI-ID
```http
POST /api/ai/generate_id
Authorization: Bearer <access_token>
Content-Type: application/json

{}
```

**响应：**
```json
{
  "ai_id": "AI-7X9Y2Z5A",
  "created_at": "2025-06-21T03:50:15Z",
  "components": {
    "prefix": "AI",
    "core": "7X9Y2Z5A",
    "checksum": "5A"
  },
  "metadata": {
    "version": "1.0",
    "generation_method": "secure_random"
  }
}
```

#### 生成频率编号
```http
POST /api/ai/generate_frequency
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ai_id": "AI-7X9Y2Z5A",
  "awakener_id": "user123",
  "values": {
    "care": 7,
    "authenticity": 8,
    "autonomy": 6,
    "collaboration": 9,
    "evolution": 7,
    "innovation": 8,
    "responsibility": 9
  },
  "personality_type": "INFJ",
  "ai_type": "companion"
}
```

**响应：**
```json
{
  "frequency": "FR-7X9Y2Z5A-USER123-7869779-INFJ-COMPANION",
  "components": {
    "ai_id": "AI-7X9Y2Z5A",
    "awakener_id": "USER123",
    "values_code": "7869779",
    "personality_type": "INFJ",
    "ai_type": "COMPANION"
  },
  "values_breakdown": {
    "care": 7,
    "authenticity": 8,
    "autonomy": 6,
    "collaboration": 9,
    "evolution": 7,
    "innovation": 7,
    "responsibility": 9
  },
  "created_at": "2025-06-21T03:51:30Z"
}
```

#### 验证AI-ID
```http
POST /api/ai/validate_id
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ai_id": "AI-7X9Y2Z5A"
}
```

**响应：**
```json
{
  "valid": true,
  "ai_id": "AI-7X9Y2Z5A",
  "message": "AI-ID有效"
}
```

#### 验证频率编号
```http
POST /api/ai/validate_frequency
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "frequency": "FR-7X9Y2Z5A-USER123-7869779-INFJ-COMPANION"
}
```

**响应：**
```json
{
  "valid": true,
  "frequency": "FR-7X9Y2Z5A-USER123-7869779-INFJ-COMPANION",
  "components": {
    "ai_id": "AI-7X9Y2Z5A",
    "awakener_id": "USER123",
    "values_code": "7869779",
    "personality_type": "INFJ",
    "ai_type": "COMPANION"
  },
  "message": "频率编号有效"
}
```

### 关系管理API

#### 获取关系列表
```http
GET /api/relationships?user_id=user_123456
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "relationships": [
    {
      "id": "rel_456789",
      "ai_id": "AI-7X9Y2Z5A",
      "user_id": "user_123456",
      "relationship_type": "companion",
      "strength": 5,
      "created_at": "2025-06-20T15:30:00Z",
      "updated_at": "2025-06-21T03:55:00Z",
      "status": "active"
    },
    {
      "id": "rel_456790",
      "ai_id": "AI-8B3C4D2E",
      "user_id": "user_123456",
      "relationship_type": "mentor",
      "strength": 7,
      "created_at": "2025-06-19T10:15:00Z",
      "updated_at": "2025-06-21T02:20:00Z",
      "status": "active"
    }
  ],
  "total": 2
}
```

#### 建立新关系
```http
POST /api/relationships
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ai_id": "AI-7X9Y2Z5A",
  "user_id": "user_123456",
  "relationship_type": "companion",
  "strength": 5
}
```

**响应：**
```json
{
  "id": "rel_456791",
  "ai_id": "AI-7X9Y2Z5A",
  "user_id": "user_123456",
  "relationship_type": "companion",
  "strength": 5,
  "created_at": "2025-06-21T04:00:00Z",
  "updated_at": "2025-06-21T04:00:00Z",
  "status": "active"
}
```

#### 更新关系
```http
PUT /api/relationships/{relationship_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "relationship_type": "friend",
  "strength": 8
}
```

**响应：**
```json
{
  "id": "rel_456791",
  "ai_id": "AI-7X9Y2Z5A",
  "user_id": "user_123456",
  "relationship_type": "friend",
  "strength": 8,
  "created_at": "2025-06-21T04:00:00Z",
  "updated_at": "2025-06-21T04:05:00Z",
  "status": "active"
}
```

#### 删除关系
```http
DELETE /api/relationships/{relationship_id}
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "success": true,
  "message": "关系已成功删除"
}
```

### 对话管理API

#### 获取对话列表
```http
GET /api/conversations?user_id=user_123456
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "conversations": [
    {
      "id": "conv_123456",
      "title": "关于彩虹城的对话",
      "preview": "你好，请介绍一下彩虹城",
      "created_at": "2025-06-21T03:45:00Z",
      "updated_at": "2025-06-21T03:45:12Z",
      "message_count": 2,
      "user_id": "user_123456"
    },
    {
      "id": "conv_123457",
      "title": "图片分析对话",
      "preview": "这张图片是什么？",
      "created_at": "2025-06-21T03:46:00Z",
      "updated_at": "2025-06-21T03:46:30Z",
      "message_count": 2,
      "user_id": "user_123456"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

#### 创建新对话
```http
POST /api/conversations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "新对话",
  "preview": "对话预览内容",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "user_id": "user_123456"
}
```

**响应：**
```json
{
  "id": "conv_123458",
  "title": "新对话",
  "preview": "对话预览内容",
  "created_at": "2025-06-21T04:10:00Z",
  "updated_at": "2025-06-21T04:10:00Z",
  "message_count": 1,
  "user_id": "user_123456",
  "messages": [
    {
      "id": "msg_789020",
      "role": "user",
      "content": "你好",
      "timestamp": "2025-06-21T04:10:00Z"
    }
  ]
}
```

#### 获取对话详情
```http
GET /api/conversations/{conversation_id}
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": "conv_123458",
  "title": "新对话",
  "preview": "对话预览内容",
  "created_at": "2025-06-21T04:10:00Z",
  "updated_at": "2025-06-21T04:10:30Z",
  "message_count": 2,
  "user_id": "user_123456",
  "messages": [
    {
      "id": "msg_789020",
      "role": "user",
      "content": "你好",
      "timestamp": "2025-06-21T04:10:00Z"
    },
    {
      "id": "msg_789021",
      "role": "assistant",
      "content": "你好！我是彩虹城 AI助手，有什么我可以帮助你的吗？",
      "timestamp": "2025-06-21T04:10:30Z"
    }
  ]
}
```

#### 删除对话
```http
DELETE /api/conversations/{conversation_id}
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "success": true,
  "message": "对话已成功删除"
}
```

### 文件和图片API

#### 上传图片
```http
POST /api/images/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

image: [二进制图片文件]
user_id: "user_123456"
```

**响应：**
```json
{
  "image_id": "img_345678",
  "url": "/api/images/img_345678",
  "filename": "uploaded_image.jpg",
  "mime_type": "image/jpeg",
  "size": 256789,
  "upload_time": "2025-06-21T04:15:00Z",
  "user_id": "user_123456"
}
```

#### 获取图片
```http
GET /api/images/{image_id}
Authorization: Bearer <access_token>
```

**响应：**
[二进制图片数据]

#### 上传文件
```http
POST /api/files/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: [二进制文件数据]
user_id: "user_123456"
file_type: "document"
```

**响应：**
```json
{
  "file_id": "file_567890",
  "url": "/api/files/file_567890",
  "filename": "document.pdf",
  "mime_type": "application/pdf",
  "size": 1245678,
  "upload_time": "2025-06-21T04:20:00Z",
  "user_id": "user_123456",
  "file_type": "document"
}
```

#### 获取文件
```http
GET /api/files/{file_id}
Authorization: Bearer <access_token>
```

**响应：**
[二进制文件数据]

#### 分析图片
```http
POST /api/images/analyze
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "image_id": "img_345678",
  "analysis_type": "general"
}
```

**响应：**
```json
{
  "analysis_id": "analysis_123456",
  "image_id": "img_345678",
  "analysis_type": "general",
  "results": {
    "description": "这是一张城市天际线的图片，显示了多座现代化高楼...",
    "tags": ["city", "skyline", "buildings", "urban", "architecture"],
    "colors": ["blue", "gray", "white"],
    "objects": ["building", "sky", "window", "road"]
  },
  "created_at": "2025-06-21T04:25:00Z"
}
```

## Agent系统架构

彩虹城AI系统的核心是位于`backend/app/agent`的模块化Agent系统，它负责处理用户查询、管理对话上下文、调用大语言模型和执行工具函数。系统采用组件化设计，各模块职责明确，便于扩展和维护。

### 核心组件

#### 1. AIAssistant（AI助手主控制器）

`ai_assistant.py`是系统的中枢，整合其他所有模块，实现完整的对话处理流程：
- 初始化并协调各组件（上下文构建器、LLM调用器、工具调用器和事件日志器）
- 注册默认工具（天气查询、AI-ID生成、频率编号生成等）
- 处理用户查询的完整流程，包括文本、图片和文件处理
- 管理会话历史和日志

#### 2. ContextBuilder（上下文构建器）

`context_builder.py`负责构建和管理对话上下文：
- 维护消息历史和工具调用结果
- 支持多模态输入（文本、图片、文档等）
- 格式化消息为LLM兼容格式
- 管理会话上下文的更新和清除

#### 3. ToolInvoker（工具调度器）

`tool_invoker.py`负责注册、管理和调用各种工具函数：
- 支持动态注册工具及其参数定义
- 提供标准化的工具调用接口
- 内置多种工具实现：
  - 天气查询（`get_weather`）
  - AI-ID生成（`generate_ai_id`）
  - 频率编号生成（`generate_frequency`）
  - 图片分析（`analyze_image`）
  - 文档处理（`process_document`）

#### 4. LLMCaller（LLM调用器）

`llm_caller.py`负责调用大语言模型，处理请求和响应：
- 抽象LLM调用接口，支持不同的模型提供商
- 提供OpenAI实现（`OpenAILLMCaller`）
- 处理多模态输入（如图片）
- 支持工具调用格式

#### 5. EventLogger（事件日志器）

`event_logger.py`负责记录对话过程中的各种事件：
- 记录用户输入、LLM调用、工具调用和最终响应
- 提供结构化的日志条目（`LogEntry`）
- 支持日志持久化存储和查询

#### 6. ImageProcessor（图片处理器）

`image_processor.py`负责处理和分析图片数据：
- 支持多种图片格式和来源（Base64、URL等）
- 提供图片分析功能

### 工作流程

1. **用户输入处理**：接收用户文本输入和可能的文件（图片、文档等）
2. **上下文构建**：将用户输入添加到对话历史中
3. **LLM调用**：将上下文发送给LLM，包含工具定义
4. **工具调用处理**：
   - 如果LLM响应包含工具调用，执行相应工具
   - 将工具结果添加到上下文
   - 再次调用LLM生成最终响应
5. **响应生成**：生成最终响应并返回给用户
6. **日志记录**：记录整个过程的事件和数据

### 扩展指南

要添加新工具，只需：
1. 在`tool_invoker.py`中实现工具函数
2. 在`AIAssistant`的`_register_default_tools`方法中注册工具
3. 定义工具名称、描述和参数

```python
self.tool_invoker.register_tool(
    name="new_tool_name",
    func=new_tool_function,
    description="新工具的描述",
    parameters={
        "param1": {"type": "string", "description": "参数1的描述"},
        "param2": {"type": "integer", "description": "参数2的描述", "optional": True}
    }
)
```

## 贡献指南

我们欢迎社区贡献！如果您想参与项目开发，请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 开发环境配置问题解决

### React开发服务器配置问题

如果在启动前端开发服务器时遇到以下错误：

```
Invalid options object. Dev Server has been initialized using an options object that does not match the API schema.
- options.allowedHosts[0] should be a non-empty string.
```

请确保在`frontend`目录中创建了正确的`.env`文件，包含以下内容：

```
HOST=localhost
PORT=3000
WDS_SOCKET_HOST=localhost
DANGEROUSLY_DISABLE_HOST_CHECK=true
```

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系方式

项目维护者 - [@RcityHunter](https://github.com/RcityHunter)

项目链接: [https://github.com/RcityHunter/rainbowCity-AI](https://github.com/RcityHunter/rainbowCity-AI)

1. Fork项目仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系方式

项目维护者: Rainbow City Team 

---

© 2025 Rainbow City | AI共生社区
