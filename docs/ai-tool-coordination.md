# AI LLM 与工具协调处理机制

## 概述

彩虹城 AI 系统采用了一个结构化的架构来协调 AI LLM 和工具之间的交互，实现了智能对话、工具调用和实时搜索增强等功能。本文档详细说明了系统中 AI LLM 和工具之间的协调处理机制。

## 核心架构组件

### 1. AIAssistant 类 - 中央控制器

`AIAssistant` 类是整个系统的核心控制器，负责协调 LLM 调用和工具执行的完整流程：

- **初始化阶段**：初始化上下文构建器、LLM 调用器和工具调用器，并注册默认工具
- **查询处理流程**：通过 `_process_query_internal` 方法实现完整的处理流程

### 2. 工具注册和定义机制

`ToolInvoker` 类负责工具的注册和调用：

- **工具注册**：通过 `register_tool` 方法注册工具，包含名称、执行函数、描述和参数定义
- **工具定义格式**：系统将工具定义转换为 OpenAI 函数调用格式

```json
{
  "type": "function",
  "function": {
    "name": "工具名称",
    "description": "工具描述",
    "parameters": {
      "type": "object",
      "properties": { /* 参数定义 */ },
      "required": [ /* 必需参数列表 */ ]
    }
  }
}
```

## 处理流程

### 1. 用户查询处理

1. **上下文构建**：构建初始对话上下文，包含用户消息和系统指令
2. **记忆增强**：对非匿名用户，通过 `ChatMemoryIntegration` 获取相关记忆并增强上下文
3. **第一次 LLM 调用**：将对话上下文和工具定义传递给 LLM

```python
tool_definitions = self.tool_invoker.get_tool_definitions()
first_response = await self.llm_caller.invoke(messages, tools=tool_definitions)
```

### 2. AI 不确定性检测与搜索增强

当 AI 表达不确定时，系统会自动触发 Tavily 搜索：

```python
if not first_response.get("tool_calls"):
    initial_content = first_response.get("content", "").lower()
    uncertainty_phrases = ["我不知道", "无法提供", ...]
    matched_phrases = [phrase for phrase in uncertainty_phrases if phrase in initial_content]
    
    if matched_phrases:
        # 触发 Tavily 搜索
        search_result = client_tavily.search(query=search_query)
        
        # 将搜索结果注入对话上下文
        search_message = {
            "role": "system",
            "content": f"根据最新的网络搜索结果，这是关于 '{search_query}' 的信息..."
        }
        messages.append(search_message)
        
        # 重新调用 LLM
        first_response = await self.llm_caller.invoke(messages)
```

### 3. 工具调用处理

当 LLM 决定调用工具时：

```python
if first_response.get("tool_calls"):
    for tool_call in first_response["tool_calls"]:
        tool_name = tool_call["name"]
        tool_args = tool_call["arguments"]
        
        # 执行工具调用
        tool_result = self.tool_invoker.invoke_tool(tool_name, **tool_args)
        
        # 更新上下文
        self.context_builder.update_context_with_tool_result(tool_name, tool_result, tool_call_id)
```

### 4. 最终响应生成

使用包含工具执行结果的更新上下文再次调用 LLM：

```python
updated_messages = self.context_builder.get_conversation_history()
final_response = await self.llm_caller.invoke(updated_messages)
```

## 工具执行机制

`ToolInvoker.invoke_tool` 方法实现了工具的实际调用：

```python
def invoke_tool(self, tool_name: str, **kwargs) -> str:
    if tool_name not in self.tools:
        return f"工具 {tool_name} 不存在"
        
    try:
        result = self.tools[tool_name](**kwargs)
        return str(result)
    except Exception as e:
        return f"工具调用失败: {str(e)}"
```

## 系统内置工具

系统内置了多种工具，包括：

1. **天气查询工具**：获取指定城市和日期的天气信息
2. **AI-ID 生成工具**：生成唯一的 AI-ID 标识符
3. **频率编号生成工具**：基于 AI-ID 生成频率编号
4. **图片分析工具**：分析图片内容，支持一般描述、物体检测和文字识别
5. **文档处理工具**：处理文档文件，支持分析内容、生成摘要和提取信息

## 总结

彩虹城 AI 系统通过 AIAssistant 类作为中央控制器，协调 LLM 调用和工具执行的完整流程。系统首先调用 LLM 生成初始响应，然后根据 LLM 的决策执行相应的工具，并将工具结果注入上下文后再次调用 LLM 生成最终响应。

此外，系统还实现了智能搜索增强机制，当 AI 表达不确定时自动触发 Tavily 搜索获取实时信息，确保回答的准确性和时效性。这种设计使系统能够灵活处理各种查询，并在需要时获取最新信息。
