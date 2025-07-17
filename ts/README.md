# Zilliz 知识库管理系统 (TypeScript版)

基于 Zilliz 云服务和 Qwen 向量化模型的智能知识库管理系统的 TypeScript 实现。

## 🚀 功能特性

- **向量数据库管理**: 基于 Zilliz 云服务的高性能向量存储
- **RESTful API 集成**: 使用 Zilliz RESTful API 替代 Node.js SDK，提供更稳定的连接
- **智能文本向量化**: 集成 Qwen/通义千问 API 进行文本嵌入
- **语义搜索**: 支持基于向量相似度的智能搜索
- **知识库构建**: 自动化的知识条目管理和索引
- **TypeScript 支持**: 完整的类型安全和开发体验
- **连接重试机制**: 内置智能重试和错误处理

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

## 🔧 技术架构更新

### v2.0 重要更新

- **迁移到 RESTful API**: 从 `@zilliz/milvus2-sdk-node` 迁移到 Zilliz RESTful API
- **更稳定的连接**: 解决了 Node.js SDK 的 gRPC 连接超时问题
- **更好的错误处理**: 增强的错误诊断和重试机制
- **简化的依赖**: 移除了复杂的 gRPC 依赖，使用轻量级的 axios

## 📦 核心模块

- **`zilliz.ts`**: Zilliz RESTful API 管理
- **`vectorizer.ts`**: Qwen文本向量化
- **`knowledgeManager.ts`**: 知识库管理核心
- **`main.ts`**: 主程序和使用示例

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 环境配置

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要信息：
```env
# Zilliz配置
ZILLIZ_ENDPOINT=https://your-cluster-endpoint.zillizcloud.com
ZILLIZ_TOKEN=your_zilliz_token_here

# Qwen/通义千问配置
QWEN_API_KEY=your_qwen_api_key_here
DASHSCOPE_API_KEY=your_dashscope_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3. 编译和运行

```bash
# 编译TypeScript
npm run build

# 运行编译后的代码
npm start

# 或者直接运行TypeScript（开发模式）
npm run dev
```

### 4. 基础使用

```typescript
import { KnowledgeManager } from './src/knowledgeManager';

async function example() {
  // 1. 创建知识库管理器
  const manager = new KnowledgeManager('my_knowledge');
  
  // 2. 向量化并存储文本
  const docId = await manager.vectorizeAndStore(
    'Python是一种高级编程语言',
    {
      topic: '编程',
      weight: 1.0,
      title: 'Python介绍',
      tags: ['编程', 'Python']
    }
  );
  console.log(`存储成功，文档ID: ${docId}`);

  // 3. 检索相关知识
  const results = await manager.searchSimilar('什么是Python？', 5);
  for (const result of results) {
    console.log(`相似度: ${result.similarity_score.toFixed(4)}`);
    console.log(`内容: ${result.text}`);
  }
}
```

## 🎯 核心API

### KnowledgeManager 类

#### 构造函数
```typescript
constructor(collectionName: string = 'knowledge_base')
```

#### 向量化存储方法
```typescript
async vectorizeAndStore(
  text: string,
  metadata: {
    topic: string;
    weight: number;
    title: string;
    tags: string[];
  }
): Promise<string>
```

**功能**: 输入字符串，生成向量并注入Zilliz向量库

**参数**:
- `text`: 要存储的文本内容
- `metadata`: 元数据信息，包含主题、权重、标题、标签

**返回**: 文档ID

#### 知识检索方法
```typescript
async searchSimilar(
  queryText: string,
  limit: number = 5,
  scoreThreshold: number = 0.0
): Promise<KnowledgeSearchResult[]>
```

**功能**: 输入字符串，生成向量，完成Zilliz检索，返回结果

**参数**:
- `queryText`: 查询文本
- `limit`: 返回结果数量限制
- `scoreThreshold`: 相似度阈值

**返回**: 检索结果列表

#### 批量处理方法
```typescript
async batchVectorizeAndStore(
  texts: string[],
  metadatas: Array<{
    topic: string;
    weight: number;
    title: string;
    tags: string[];
  }>
): Promise<string[]>
```

**功能**: 批量向量化并存储多个文本

#### 获取统计信息
```typescript
async getCollectionInfo(): Promise<CollectionInfo>
```

**功能**: 获取知识库集合的详细信息和统计数据

## 📖 使用示例

### 基础示例

```typescript
import { KnowledgeManager } from './src/knowledgeManager';

async function basicExample() {
  const manager = new KnowledgeManager('ai_knowledge');

  // 存储知识
  const knowledgeTexts = [
    '机器学习是人工智能的一个分支',
    '深度学习使用神经网络进行学习',
    '自然语言处理帮助计算机理解人类语言'
  ];

  for (const text of knowledgeTexts) {
    const docId = await manager.vectorizeAndStore(text, {
      topic: 'AI',
      weight: 1.0,
      title: 'AI基础知识',
      tags: ['人工智能', '机器学习']
    });
    console.log(`存储: ${text.substring(0, 20)}... -> ${docId}`);
  }

  // 检索知识
  const query = '什么是机器学习？';
  const results = await manager.searchSimilar(query);

  console.log(`查询: ${query}`);
  results.forEach((result, index) => {
    console.log(`${index + 1}. ${result.text} (相似度: ${result.similarity_score.toFixed(4)})`);
  });
}
```

### 批量处理示例

```typescript
import { KnowledgeManager } from './src/knowledgeManager';

async function batchExample() {
  const manager = new KnowledgeManager('batch_knowledge');

  // 批量存储
  const texts = [
    'TypeScript是JavaScript的超集',
    'Node.js是服务端JavaScript运行时',
    'React是用于构建用户界面的库'
  ];
  
  const metadatas = [
    { topic: '编程语言', weight: 1.0, title: 'TypeScript', tags: ['TypeScript', '编程'] },
    { topic: '运行时', weight: 1.0, title: 'Node.js', tags: ['Node.js', '服务端'] },
    { topic: '前端框架', weight: 1.0, title: 'React', tags: ['React', '前端'] }
  ];

  const docIds = await manager.batchVectorizeAndStore(texts, metadatas);
  console.log(`批量存储完成，文档IDs: ${docIds}`);

  // 高级检索
  const results = await manager.searchSimilar(
    '前端开发技术',
    10,
    0.5
  );

  // 获取统计信息
  const stats = await manager.getCollectionInfo();
  console.log(`知识库统计: ${JSON.stringify(stats, null, 2)}`);
}
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
npx ts-node src/zilliz.ts

# 测试向量化功能
npx ts-node src/vectorizer.ts

# 测试知识库管理
npx ts-node src/knowledgeManager.ts

# 运行完整示例
npm run dev
```

## 📁 项目结构

```
ts/
├── .env.example          # 环境变量模板
├── package.json          # 项目配置和依赖
├── tsconfig.json         # TypeScript配置
├── README.md            # 项目文档
├── src/
│   ├── zilliz.ts        # Zilliz管理模块
│   ├── vectorizer.ts    # 文本向量化模块
│   ├── knowledgeManager.ts # 知识库管理模块
│   └── main.ts          # 主程序和示例
└── dist/                # 编译输出目录
```

## 🔄 开发脚本

```bash
# 安装依赖
npm install

# 编译TypeScript
npm run build

# 运行编译后的代码
npm start

# 开发模式（直接运行TypeScript）
npm run dev

# 清理编译输出
npm run clean

# 运行测试
npm test
```

## 🆚 与Python版本的差异

### 优势
- **类型安全**: 完整的TypeScript类型定义，编译时错误检查
- **现代语法**: 使用async/await、ES6+语法
- **包管理**: 使用npm生态系统
- **开发体验**: 更好的IDE支持和代码提示

### 兼容性
- **API接口**: 保持与Python版本相同的核心API
- **数据格式**: 兼容的数据结构和存储格式
- **功能特性**: 完整实现Python版本的所有功能

## ⚠️ 注意事项

1. **API密钥安全**: 请妥善保管API密钥，不要提交到版本控制
2. **网络连接**: 确保能够访问Zilliz和Qwen服务
3. **向量维度**: Qwen text-embedding-v3 默认1024维
4. **相似度计算**: 使用余弦相似度进行向量比较
5. **集合管理**: 系统会自动创建和管理向量集合
6. **Node.js版本**: 需要Node.js 16.0.0或更高版本

## 🐛 故障排除

### 常见问题

1. **编译错误**
   - 检查TypeScript版本
   - 确认所有依赖已安装
   - 验证tsconfig.json配置

2. **连接失败**
   - 检查网络连接
   - 验证API密钥
   - 确认服务端点正确

3. **向量化失败**
   - 检查Qwen API密钥
   - 确认API配额充足
   - 验证文本格式

4. **检索无结果**
   - 降低相似度阈值
   - 检查集合是否有数据
   - 尝试不同的查询文本

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！