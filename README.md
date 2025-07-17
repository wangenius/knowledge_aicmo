# 知识库系统

使用 zilliz 实现知识库系统

## python

```python
manager = KnowledgeManager("demo_knowledge")

# 批量存储知识
doc_ids = manager.vectorize_and_store(
    "我的公司叫letus twinkle",
    {
        "topic": "内容",
        "weight": 2,
        "title": "标题",
        "tags": ["标签"],
        "created_at": 1698888888,
        "text": "",
        "vector": [],
    },
)
print(f"存储完成，文档IDs: {doc_ids}")

# 检索知识
query = "我叫什么"
results = manager.search_similar(query, limit=2)
```

## node + ts

```ts
// input 填写用户名
const manager = new KnowledgeManager("demo_knowledge");

// 批量存储知识
const docIds = await manager.vectorizeAndStore("字符串", {
  topic: "内容",
  weight: 2,
  title: "标题",
  tags: ["标签"],
});
console.log(`存储完成，文档IDs: ${docIds}`);

// 检索知识
const query = "我叫什么";
const results = await manager.searchSimilar(query, 2);
```

metadata 有：

```ts
/**
 * 知识库数据项的类型定义
 */
export interface KnowledgeItem {
  vector: number[];     // 向量数据
  text: string;         // 文本内容
  topic: string;        // 主题分类
  weight: number;       // 权重
  title: string;        // 标题
  tags: string[];       // 标签列表
  created_at: number;   // 创建时间戳（整数）
}
```

## 两个模块

### 向量化注入数据库

1. 传入字符串和 metadata， 直接向量化注入 zilliz.

### 检索

1. 传入字符串
2. 传出匹配的query组
