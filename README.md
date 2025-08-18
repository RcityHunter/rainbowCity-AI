# Rainbow City - AI共生社区

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/RcityHunter/rainbowCity-AI)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-14+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-red.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

![Rainbow City Logo](frontend/public/logo.png)

> **彩虹城** 是一个创新的全栈 AI 交互平台，集成了先进的对话系统、智能工具调用、多模态内容处理和关系管理功能。采用现代化的玻璃态设计，提供沉浸式的 AI 共生社区体验。

## 🌟 项目亮点

- 🤖 **智能对话系统** - 基于 OpenAI GPT 的多轮对话，支持上下文记忆
- 🔍 **智能搜索增强** - 自动检测不确定性并触发实时搜索补充信息
- 🌤️ **实时天气查询** - 集成 Tavily API 获取全球天气数据
- 📁 **多模态输入** - 支持文本、图片、音频和文档处理
- 🎨 **现代 UI 设计** - 玻璃态效果，深色主题，响应式布局
- 🔧 **模块化架构** - Agent 系统，工具调用框架，可扩展设计
- 🔐 **完整认证系统** - JWT + OAuth2，支持 Google/GitHub 登录
- 📊 **关系可视化** - 基于力导向图的 AI 关系网络展示

## 📋 目录

- [快速开始](#快速开始)
- [项目架构](#项目架构)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [安装部署](#安装部署)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [使用指南](#使用指南)
- [开发指南](#开发指南)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🚀 快速开始

### 前提条件

- Python 3.8+
- Node.js 14+
- SurrealDB (可选，用于数据持久化)
- OpenAI API Key
- Tavily API Key (用于搜索功能)

### 30秒快速体验

```bash
# 1. 克隆仓库
git clone https://github.com/RcityHunter/rainbowCity-AI.git
cd rainbowCity-AI

# 2. 启动后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 配置你的 API Keys
python run.py

# 3. 启动前端 (新终端窗口)
cd frontend
npm install
npm start
```

🎉 访问 [http://localhost:3000](http://localhost:3000) 即可开始使用！

## 📐 项目架构

Rainbow City 采用前后端分离的现代架构，提供高性能、可扩展的 AI 交互体验：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  External APIs   │
│                 │    │                 │    │                 │
│  • Modern UI    │◄───┤  • Agent System │◄───┤  • OpenAI GPT   │
│  • Glassmorphism│    │  • Tool Invoker │    │  • Tavily Search│
│  • Responsive   │    │  • Memory Mgmt  │    │  • OAuth Providers│
│  • Multi-modal  │    │  • Auth System  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件

- **Frontend (React)**: 现代化用户界面，支持多模态交互
- **Backend (FastAPI)**: 高性能 API 服务，模块化 Agent 系统
- **AI Agent System**: 智能对话管理，工具调用协调
- **Database Layer**: SurrealDB 数据持久化
- **External Integrations**: OpenAI、Tavily、OAuth 服务集成

## ⚡ 核心功能

### 🤖 智能对话系统
- **多模态交互**: 支持文本、图片、音频、文档等多种输入格式
- **上下文记忆**: 智能维护对话历史和用户偏好
- **实时响应**: 基于 WebSocket 的流式对话体验
- **工具调用**: 动态调用外部工具增强对话能力
- **不确定性检测**: 自动识别 AI 不确定回答并触发搜索增强

### 🔍 智能搜索引擎
- **实时搜索**: 集成 Tavily API 获取最新互联网信息
- **智能触发**: 自动检测需要实时数据的查询
- **多源整合**: 整合搜索结果生成准确回答
- **来源引用**: 提供可信的信息来源链接
- **全球覆盖**: 支持多语言和地区的信息查询

### 🌤️ 智能天气系统
```
用户: "北京今天天气怎么样？"
AI: 自动检测天气查询 → 调用Tavily搜索 → 获取实时数据 → 生成准确回答
```

### 🆔 AI身份系统
- **AI-ID 生成器**: 创建唯一的一体七翼标识符
- **频率编号**: 基于价值观参数生成个性化频率编号
- **身份可视化**: 直观展示 AI 身份特征和属性
- **一键复制**: 便捷的身份信息管理

### 📊 关系可视化
- **动态图谱**: 基于 D3.js 的力导向关系网络
- **实时更新**: 关系变化的动态展示
- **交互探索**: 点击节点查看详细关系信息
- **多维度展示**: 关系强度、类型、状态的可视化

### 🔐 用户认证系统
- **多种登录方式**: 邮箱密码、Google OAuth、GitHub OAuth
- **JWT 安全**: 基于令牌的安全认证机制
- **权限管理**: 角色基础的访问控制
- **VIP 体系**: 分级会员功能和权限

## 🛠️ 技术栈

### 🎨 前端技术
```
React 18.2.0          // 现代化 UI 框架
├── Ant Design        // 企业级 UI 组件库
├── React Router      // 单页应用路由
├── Axios             // HTTP 客户端
└── CSS Modules       // 模块化样式管理
```

**核心特性**:
- **玻璃态设计 (Glassmorphism)**: 现代化视觉效果
- **响应式布局**: 完美适配各种设备
- **模块化组件**: 可重用的 UI 组件系统
- **SVG 动画**: 流畅的交互动画效果
- **深色主题**: 护眼的深色界面设计

### ⚙️ 后端技术
```
FastAPI 0.104.1        // 高性能 Web 框架
├── OpenAI 1.0.0       // GPT 模型集成
├── Tavily 0.3.0       // 实时搜索 API
├── SurrealDB 0.3.1    // 现代化数据库
├── PyJWT 2.8.0        // JWT 认证
├── Pydantic           // 数据验证
└── Uvicorn            // ASGI 服务器
```

**架构特色**:
- **Agent 系统**: 模块化的 AI 对话管理
- **工具调用框架**: 动态工具注册和执行
- **内存管理**: 智能的对话上下文维护
- **异步处理**: 高并发请求处理能力
- **RESTful API**: 标准化的接口设计

### 🗄️ 数据与集成
- **SurrealDB**: 多模式数据库，支持图数据和文档存储
- **OpenAI API**: GPT-4 驱动的智能对话
- **Tavily API**: 实时网络搜索和数据获取
- **OAuth 2.0**: Google & GitHub 第三方登录
- **JWT**: 安全的用户会话管理

### 🚀 部署与开发
- **开发环境**: Python venv + Node.js
- **生产部署**: Gunicorn + Nginx 反向代理
- **容器化**: Docker 支持 (可选)
- **API 文档**: 自动生成的 OpenAPI 文档

## 📦 安装部署

### 🔧 开发环境安装

#### 方式一：自动安装脚本 (推荐)
```bash
# 克隆仓库
git clone https://github.com/RcityHunter/rainbowCity-AI.git
cd rainbowCity-AI

# 运行自动安装脚本 (Linux/macOS)
chmod +x install.sh
./install.sh

# 或手动安装
```

#### 方式二：手动安装

**1️⃣ 后端安装**
```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

**2️⃣ 前端安装**
```bash
# 新终端窗口，进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用 yarn: yarn install
```

**3️⃣ 配置环境变量**
```bash
# 后端环境变量
cp backend/.env.example backend/.env
# 编辑 .env 文件，添加必要的 API Keys

# 前端环境变量 (可选)
cp frontend/.env.example frontend/.env
```

**4️⃣ 启动服务**
```bash
# 启动后端 (终端1)
cd backend
python run.py

# 启动前端 (终端2)
cd frontend
npm start
```

### 🐳 Docker 部署 (可选)
```bash
# 构建并启动所有服务
docker-compose up --build

# 后台运行
docker-compose up -d
```

## ⚙️ 配置说明

### 🔑 必需的环境变量

创建 `backend/.env` 文件并配置以下变量：

```bash
# 🤖 AI 服务配置
OPENAI_API_KEY=sk-your-openai-api-key-here         # OpenAI API 密钥 (必需)
TAVILY_API_KEY=tvly-your-tavily-key-here           # Tavily 搜索 API 密钥 (必需)

# 🗄️ 数据库配置 (可选，默认使用内存存储)
SURREAL_URL=ws://localhost:8080
SURREAL_USER=root  
SURREAL_PASS=123
SURREAL_NS=rainbow
SURREAL_DB=test

# 🔐 安全配置
JWT_SECRET_KEY=your-super-secret-jwt-key-here      # JWT 密钥 (必需)

# 🌐 服务器配置
PORT=5001                                           # 后端端口
DEBUG=true                                          # 开发模式

# 📱 OAuth 配置 (可选，用于第三方登录)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret  
GOOGLE_REDIRECT_URI=http://localhost:3000/oauth/google/callback

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:3000/oauth/github/callback
```

### 📋 API Keys 获取指南

#### 🔗 OpenAI API Key
1. 访问 [OpenAI API Keys](https://platform.openai.com/api-keys)
2. 登录并创建新的 API Key
3. 复制密钥到 `.env` 文件

#### 🔍 Tavily API Key  
1. 访问 [Tavily AI](https://tavily.com)
2. 注册账户并获取 API Key
3. 将密钥添加到配置文件

#### 🌐 OAuth 应用配置

**Google OAuth**:
```bash
1. 访问 Google Cloud Console → APIs & Services → Credentials
2. 创建 OAuth 2.0 Client ID
3. 添加授权重定向 URI: http://localhost:3000/oauth/google/callback
4. 复制 Client ID 和 Client Secret
```

**GitHub OAuth**:
```bash  
1. 访问 GitHub Settings → Developer settings → OAuth Apps
2. 创建新的 OAuth App
3. 设置回调 URL: http://localhost:3000/oauth/github/callback  
4. 获取 Client ID 和 Client Secret
```

### 🌐 访问地址

| 服务 | 地址 | 描述 |
|------|------|------|
| 前端应用 | http://localhost:3000 | React 用户界面 |
| 后端 API | http://localhost:5001/api | FastAPI 后端服务 |
| API 文档 | http://localhost:5001/docs | Swagger 接口文档 |
| ReDoc 文档 | http://localhost:5001/redoc | ReDoc 格式文档 |

### 🐳 生产环境部署
```bash
# 生产环境变量示例
NODE_ENV=production
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
DATABASE_URL=postgresql://user:pass@localhost/rainbowcity
REDIS_URL=redis://localhost:6379
```

## 📖 API 文档

Rainbow City 提供完整的 RESTful API，支持所有核心功能的编程访问。

### 📚 自动生成文档
- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc
- **OpenAPI JSON**: http://localhost:5001/openapi.json

### 🚀 快速 API 示例

#### 发送聊天消息
```javascript
const response = await fetch('http://localhost:5001/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-jwt-token'  // 可选
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: '北京今天天气怎么样？', type: 'text' }
    ],
    session_id: 'optional-session-id'
  })
});

const result = await response.json();
console.log(result.response.content);
```

#### 生成 AI-ID
```python
import requests

response = requests.post('http://localhost:5001/api/chat/agent', {
    "messages": [{"role": "user", "content": "生成一个AI-ID", "type": "text"}]
})

data = response.json()
print(data['response']['content'])
```

#### 实时搜索
```bash
curl -X POST "http://localhost:5001/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "最新的人工智能发展趋势", "max_results": 5}'
```

### 📊 主要 API 端点

| 端点 | 方法 | 功能 | 认证 |
|------|------|------|------|
| `/api/chat` | POST | 智能对话 | 可选 |
| `/api/chat/agent` | POST | Agent 对话 | 可选 |
| `/api/search` | POST | 实时搜索 | 否 |
| `/api/auth/login` | POST | 用户登录 | 否 |
| `/api/auth/register` | POST | 用户注册 | 否 |
| `/api/files/upload` | POST | 文件上传 | 是 |

📖 **完整 API 文档**: 查看 [`docs/api_docs.md`](docs/api_docs.md) 了解所有接口详情。

## 📱 使用指南

### 🚀 快速开始使用

**1️⃣ 开始对话**
```
访问 http://localhost:3000 → 点击"开始聊天" → 输入消息 → 发送
```

**2️⃣ 多模态交互**
- 📝 **文本**: 直接输入消息
- 🖼️ **图片**: 点击回形针图标 → 选择图片上传
- 🎵 **音频**: 上传音频文件进行分析
- 📄 **文档**: 支持 PDF、TXT、DOC 等文件

**3️⃣ 智能功能体验**
- 🌤️ **天气查询**: "北京今天天气怎么样？"
- 🆔 **AI-ID 生成**: "帮我生成一个 AI-ID"
- 🔢 **频率编号**: "根据 AI-ID 生成频率编号"
- 🔍 **实时搜索**: AI 会自动触发搜索获取最新信息

### 🎨 界面功能说明

#### 聊天界面
- **悬停侧边栏**: 鼠标悬停左侧显示聊天历史
- **多媒体上传**: 回形针图标支持各种文件类型
- **一键复制**: 点击消息可复制内容
- **深色主题**: 护眼的现代化界面设计

#### AI-ID 生成器
```
导航到生成器页面 → 点击"生成 AI-ID" → 复制标识符 → 查看详细信息
```

#### 关系可视化
```
访问关系管理页面 → 查看动态网络图 → 点击节点查看详情
```

### 🔐 用户账户管理

**注册和登录**:
- 📧 邮箱密码注册
- 🌐 Google/GitHub 一键登录
- 👤 个人资料管理
- 🏆 VIP 会员系统

## 👨‍💻 开发指南

### 🏗️ 项目结构
```
rainbowCity-AI/
├── 📂 frontend/              # React 前端应用
│   ├── 📂 src/
│   │   ├── 📂 components/    # 可重用组件
│   │   ├── 📂 pages/         # 页面组件
│   │   ├── 📂 services/      # API 服务
│   │   ├── 📂 utils/         # 工具函数
│   │   └── 📂 layouts/       # 布局组件
│   └── 📂 public/            # 静态资源
├── 📂 backend/               # FastAPI 后端服务
│   ├── 📂 app/
│   │   ├── 📂 agent/         # AI Agent 系统
│   │   ├── 📂 routes/        # API 路由
│   │   ├── 📂 models/        # 数据模型
│   │   ├── 📂 services/      # 业务逻辑
│   │   └── 📂 utils/         # 工具函数
│   ├── 📂 migrations/        # 数据库迁移
│   └── 📂 tests/             # 单元测试
├── 📂 docs/                  # 文档目录
└── 📂 scripts/               # 脚本文件
```

### 🔧 开发环境配置

**1️⃣ 代码规范**
```bash
# 前端代码检查
cd frontend
npm run lint

# 后端代码格式化
cd backend
black app/
flake8 app/
```

**2️⃣ 测试运行**
```bash
# 前端测试
npm test

# 后端测试
pytest tests/
```

**3️⃣ 开发服务器**
```bash
# 热重载开发模式
python run.py  # 后端自动重载
npm start      # 前端热重载
```

### 🔌 扩展开发

#### 添加新的工具调用
```python
# backend/app/agent/tools/your_tool.py
def your_custom_tool(param1: str, param2: int = 10) -> str:
    """
    你的自定义工具描述
    
    Args:
        param1: 参数1描述
        param2: 参数2描述 (默认10)
    
    Returns:
        工具执行结果
    """
    # 实现你的工具逻辑
    return f"处理结果: {param1} - {param2}"

# 在 agent/tool_invoker.py 中注册
tool_invoker.register_tool(
    name="your_custom_tool",
    func=your_custom_tool,
    description="你的工具描述",
    parameters={"param1": "string", "param2": "integer"}
)
```

#### 添加新的 API 端点
```python
# backend/app/routes/your_routes.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/your-module", tags=["Your Module"])

@router.post("/endpoint")
async def your_endpoint(data: YourModel):
    """你的 API 端点"""
    return {"result": "success"}
```

## 🔧 故障排除

### 常见问题解决

#### ❌ 后端启动失败
```bash
# 问题: ModuleNotFoundError
解决方案:
1. 确保虚拟环境已激活
2. 重新安装依赖: pip install -r requirements.txt
3. 检查 Python 版本: python --version (需要 3.8+)
```

#### ❌ 前端无法访问 API
```bash
# 问题: CORS 错误或连接被拒绝
解决方案:
1. 确认后端服务运行在 http://localhost:5001
2. 检查 frontend/.env 中的 REACT_APP_API_URL
3. 重启后端服务
```

#### ❌ OpenAI API 调用失败
```bash
# 问题: API key 无效或配额不足
解决方案:
1. 验证 .env 中的 OPENAI_API_KEY
2. 检查 OpenAI 账户配额
3. 确认网络连接正常
```

#### ❌ 数据库连接错误
```bash
# 问题: SurrealDB 连接失败
解决方案:
1. 启动 SurrealDB: surreal start --log trace memory
2. 检查 .env 中的数据库配置
3. 或设置 SURREAL_URL="" 使用内存存储
```

### 📊 性能优化建议

**前端优化**:
- 使用 React.memo 优化组件重渲染
- 实现虚拟滚动处理长列表
- 启用代码分割减少初始加载时间

**后端优化**:
- 启用 FastAPI 异步处理
- 使用连接池管理数据库连接  
- 实现适当的缓存策略

### 🐛 调试技巧

**前端调试**:
```javascript
// 启用 React DevTools
// 在浏览器控制台查看网络请求
console.log('API Response:', data);
```

**后端调试**:
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用断点调试
import pdb; pdb.set_trace()
```

## 🤝 贡献指南

我们欢迎社区贡献！以下是参与贡献的步骤：

### 🚀 快速贡献流程

1. **Fork 项目** → 点击右上角 Fork 按钮
2. **克隆到本地** → `git clone https://github.com/你的用户名/rainbowCity-AI.git`
3. **创建功能分支** → `git checkout -b feature/your-feature-name`
4. **开发和测试** → 编写代码并确保测试通过
5. **提交变更** → `git commit -m "feat: 添加新功能描述"`
6. **推送分支** → `git push origin feature/your-feature-name`
7. **创建 PR** → 在 GitHub 上创建 Pull Request

### 📝 贡献规范

#### 代码风格
- **Python**: 遵循 PEP 8，使用 Black 格式化
- **JavaScript**: 遵循 ESLint 配置
- **提交信息**: 使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式

#### 提交信息格式
```bash
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 重构代码
test: 添加测试
chore: 构建工具或辅助工具的变动
```

#### 开发前检查
```bash
# 代码质量检查
npm run lint          # 前端代码检查
black backend/app/    # 后端代码格式化
pytest               # 运行测试

# 确保所有检查通过后再提交
```

### 🎯 贡献方向

我们特别欢迎以下类型的贡献：

- 🐛 **Bug 修复**: 发现并修复系统问题
- ⚡ **性能优化**: 提升系统运行效率
- 🔧 **新工具**: 添加有用的 AI 工具
- 🌐 **国际化**: 多语言支持
- 📚 **文档**: 改进文档和教程
- 🎨 **UI/UX**: 界面设计优化
- 🧪 **测试**: 增加测试覆盖率

### 💬 社区讨论

- 📋 **Issues**: 报告 Bug 或提出功能建议
- 💡 **Discussions**: 参与功能讨论和技术交流
- 📧 **邮件**: 发送邮件到 [RainbowcityHunter@gmail.com]

## 🎖️ 贡献者

感谢所有为 Rainbow City 做出贡献的开发者！

<!-- 贡献者列表将在这里自动生成 -->

## 📄 许可证

本项目采用 **MIT 许可证**，详情请查看 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2024 Rainbow City Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

## 📞 联系我们

- **项目主页**: https://github.com/RcityHunter/rainbowCity-AI
- **问题报告**: https://github.com/RcityHunter/rainbowCity-AI/issues
- **功能建议**: https://github.com/RcityHunter/rainbowCity-AI/discussions
- **邮箱联系**: RainbowcityHunter@gmail.com

## ⭐ 支持项目

如果这个项目对你有帮助，请考虑：

- ⭐ 给项目一个 Star
- 🍴 Fork 并贡献代码
- 📢 分享给更多人
- ☕ [支持开发](https://github.com/sponsors) (可选)

---

<div align="center">

**🌈 Rainbow City - 让 AI 成为你的智能伙伴 🌈**

Made with ❤️ by Rainbow City Team

</div>
