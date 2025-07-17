# 知识库管理系统

基于Zilliz云服务和Qwen向量化模型的智能知识库管理系统。

## 🌟 功能特性

- 🤖 **智能向量化**: 使用Qwen模型将文本转换为高维向量
- 🗄️ **向量存储**: 基于Zilliz云服务的高性能向量数据库
- 🔍 **语义检索**: 支持自然语言查询的相似度搜索
- 📚 **知识管理**: 完整的知识库生命周期管理
- 🚀 **简单易用**: 提供简洁的API接口
- 🔐 **多种认证**: 支持多种Zilliz认证方式

## 🏗️ 系统架构

```
用户输入文本
     ↓
  Qwen向量化
     ↓
  Zilliz存储
     ↓
   语义检索
     ↓
   返回结果
```

## 📦 核心模块

- **`zilliz.py`**: Zilliz云服务管理
- **`vectorizer.py`**: Qwen文本向量化
- **`knowledge_manager.py`**: 知识库管理核心
- **`knowledge_api.py`**: 用户API接口

## 🚀 快速开始

### 1. 环境配置

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要信息：
```env
# Zilliz配置
ZILLIZ_ENDPOINT=https://your-cluster-endpoint.zillizcloud.com
ZILLIZ_TOKEN=your_zilliz_token_here

# Qwen配置
QWEN_API_KEY=your_qwen_api_key_here
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 基础使用

```python
from knowledge_api import vectorize_and_store, search_knowledge

# 1. 向量化并存储文本
doc_id = vectorize_and_store(
    "Python是一种高级编程语言",
    {"category": "编程", "language": "Python"}
)
print(f"存储成功，文档ID: {doc_id}")

# 2. 检索相关知识
results = search_knowledge("什么是Python？", limit=5)
for result in results:
    print(f"相似度: {result['similarity_score']:.4f}")
    print(f"内容: {result['text']}")
```

## 🎯 核心API

### 向量化存储函数

```python
vectorize_and_store(text: str, metadata: dict = None) -> str
```

**功能**: 输入字符串，生成向量并注入Zilliz向量库

**参数**:
- `text`: 要存储的文本内容
- `metadata`: 可选的元数据信息

**返回**: 文档ID

### 知识检索函数

```python
search_knowledge(query: str, limit: int = 5, score_threshold: float = 0.0) -> List[Dict]
```

**功能**: 输入字符串，生成向量，完成Zilliz检索，返回结果

**参数**:
- `query`: 查询文本
- `limit`: 返回结果数量限制
- `score_threshold`: 相似度阈值

**返回**: 检索结果列表

## 📖 使用示例

### 基础示例

```python
from knowledge_api import vectorize_and_store, search_knowledge

# 存储知识
knowledge_texts = [
    "机器学习是人工智能的一个分支",
    "深度学习使用神经网络进行学习",
    "自然语言处理帮助计算机理解人类语言"
]

for text in knowledge_texts:
    doc_id = vectorize_and_store(text, {"domain": "AI"})
    print(f"存储: {text[:20]}... -> {doc_id}")

# 检索知识
query = "什么是机器学习？"
results = search_knowledge(query)

print(f"查询: {query}")
for i, result in enumerate(results, 1):
    print(f"{i}. {result['text']} (相似度: {result['similarity_score']:.4f})")
```

### 高级示例

```python
from knowledge_api import KnowledgeAPI

# 创建专用知识库
api = KnowledgeAPI("my_knowledge_base")

# 批量存储
texts = ["文本1", "文本2", "文本3"]
metadatas = [{"type": "A"}, {"type": "B"}, {"type": "C"}]
doc_ids = api.batch_vectorize_and_store(texts, metadatas)

# 高级检索
results = api.search_knowledge(
    "查询文本", 
    limit=10, 
    score_threshold=0.5
)

# 获取统计信息
stats = api.get_stats()
print(f"知识库统计: {stats}")
```

## 🔧 配置说明

### Zilliz配置

```env
# 必需配置
ZILLIZ_ENDPOINT=https://your-cluster-endpoint.zillizcloud.com

# 认证方式（选择其一）
ZILLIZ_TOKEN=your_token                    # 推荐
ZILLIZ_API_KEY=your_api_key               # 或者
ZILLIZ_USERNAME=username                   # 或者
ZILLIZ_PASSWORD=password                   # 配合用户名
```

### Qwen配置

```env
# 必需配置
QWEN_API_KEY=your_qwen_api_key

# 可选配置
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 🧪 运行示例

```bash
# 测试Zilliz连接
python zilliz.py

# 测试向量化功能
python vectorizer.py

# 测试知识库管理
python knowledge_manager.py

# 运行完整示例
python example.py
```

## 📁 项目结构

```
knowledge/
├── .env.example          # 环境变量模板
├── .gitignore           # Git忽略文件
├── README.md            # 项目文档
├── requirements.txt     # 依赖列表
├── zilliz.py           # Zilliz管理模块
├── vectorizer.py       # 文本向量化模块
├── knowledge_manager.py # 知识库管理模块
├── knowledge_api.py    # API接口模块
└── example.py          # 使用示例
```

## ⚠️ 注意事项

1. **API密钥安全**: 请妥善保管API密钥，不要提交到版本控制
2. **网络连接**: 确保能够访问Zilliz和Qwen服务
3. **向量维度**: Qwen text-embedding-v3 默认1024维
4. **相似度计算**: 使用余弦相似度进行向量比较
5. **集合管理**: 系统会自动创建和管理向量集合

## 🐛 故障排除

### 常见问题

1. **连接失败**
   - 检查网络连接
   - 验证API密钥
   - 确认服务端点正确

2. **向量化失败**
   - 检查Qwen API密钥
   - 确认API配额充足
   - 验证文本格式

3. **检索无结果**
   - 降低相似度阈值
   - 检查集合是否有数据
   - 尝试不同的查询文本

## 📄 许可证

MIT License