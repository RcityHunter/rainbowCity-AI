# 向量存储与语义搜索功能

本文档详细介绍了彩虹城AI系统中向量存储和语义搜索功能的实现和使用方法。

## 功能概述

向量存储功能使AI助手能够基于语义相似度而非简单的关键词匹配来检索相关记忆，显著提高了记忆检索的准确性和相关性。

主要功能包括：

1. **文本向量嵌入生成**：将文本转换为高维向量表示
2. **向量索引管理**：高效存储和检索向量
3. **语义相似度搜索**：基于向量相似度查找相关记忆
4. **混合搜索策略**：结合向量搜索和关键词搜索的优势

## 技术实现

### 1. 嵌入模型

系统使用 `sentence-transformers` 库中的预训练模型生成文本嵌入：

- 默认模型：`all-MiniLM-L6-v2`（轻量级，384维向量）
- 可选模型：`all-mpnet-base-v2`（更准确但更慢，768维向量）

模型选择可通过环境变量 `EMBEDDING_MODEL` 配置。

### 2. 向量索引

系统使用 `hnswlib` 库实现高效的近似最近邻搜索：

- 索引类型：分层可导航小世界图（HNSW）
- 相似度度量：余弦相似度（Cosine Similarity）
- 内存中索引：每种记忆类型维护单独的索引

### 3. 数据模型扩展

所有记忆模型都扩展了向量嵌入字段：

```python
class BaseMemory(BaseModel):
    # 现有字段...
    embedding: Optional[List[float]] = None  # 向量嵌入
```

查询模型也添加了向量搜索支持：

```python
class MemoryQuery(BaseModel):
    # 现有字段...
    use_vector_search: bool = False  # 是否使用向量搜索
    embedding: Optional[List[float]] = None  # 查询向量嵌入
```

### 4. 异步处理

为避免阻塞主请求流程，系统采用异步方式处理向量操作：

- 嵌入生成在后台异步进行
- 使用异步锁防止并发冲突
- 批量处理提高效率

## 使用方法

### 1. 保存记忆时生成向量嵌入

```python
# 保存用户记忆并生成向量嵌入
memory = await MemoryService.save_user_memory(
    user_id="user123",
    content="用户喜欢旅行，特别是去海边",
    memory_type="preference",
    importance=MemoryImportance.MEDIUM,
    generate_embedding=True  # 启用向量嵌入生成
)
```

### 2. 使用向量搜索查询记忆

```python
# 创建记忆查询
memory_query = MemoryQuery(
    user_id="user123",
    query="用户有什么爱好？",
    limit=5,
    sort_by="vector",  # 按向量相似度排序
    use_vector_search=True  # 启用向量搜索
)

# 执行搜索
results = await MemoryService.search_memories(memory_query)
```

### 3. 在聊天上下文中使用向量搜索

聊天记忆集成服务默认使用向量搜索检索相关记忆：

```python
# 获取与查询相关的记忆
relevant_memories = await chat_memory_integration.get_relevant_memories(
    user_id="user123",
    query="用户的旅行计划是什么？",
    limit=5  # 限制结果数量
)
```

## 配置选项

### 环境变量

- `EMBEDDING_MODEL`：指定使用的sentence-transformers模型
  - 默认值：`all-MiniLM-L6-v2`
  - 示例：`EMBEDDING_MODEL=all-mpnet-base-v2`

### 向量索引参数

在 `embedding_service.py` 中可调整以下参数：

- `max_elements`：索引最大元素数量（默认：100000）
- `ef_construction`：构建索引时的搜索深度（默认：200）
- `ef_search`：搜索时的搜索深度（默认：50）
- `M`：每个元素的最大连接数（默认：16）

## 性能考虑

1. **内存使用**：向量索引存储在内存中，随记忆数量增长
2. **模型加载时间**：首次初始化时需要加载嵌入模型
3. **批处理效率**：批量生成嵌入比单条处理更高效

## 故障排除

### 常见问题

1. **嵌入生成失败**：
   - 检查是否已安装所需依赖
   - 确认模型名称正确且可访问

2. **向量搜索返回不相关结果**：
   - 增加训练数据量
   - 尝试使用更准确的嵌入模型

3. **内存使用过高**：
   - 减少索引中的最大元素数量
   - 定期清理不再需要的记忆

### 日志调试

系统会记录向量操作的关键事件：

- 嵌入模型加载
- 向量索引创建和更新
- 搜索操作和结果

## 未来改进

1. **持久化向量索引**：在服务重启时保存和恢复索引
2. **分布式向量存储**：支持大规模部署
3. **自适应搜索策略**：根据查询特点自动选择最佳搜索方法
4. **增量学习**：随时间优化向量表示

## 依赖库

- `sentence-transformers`: 文本嵌入生成
- `hnswlib`: 高效向量索引和搜索
- `numpy`: 向量操作
- `scikit-learn`: 向量相似度计算（可选）
