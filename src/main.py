from knowledge_manager import KnowledgeManager


def main():
    """用法演示"""
    try:
        print("=== 知识库用法演示 ===")

        # 方式1：使用类接口
        print("\n1. 使用类接口:")
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

        print(f"\n查询: {query}")
        print("检索结果:")
        for i, result in enumerate(results, 1):
            print(f"{i}. 相似度: {result['similarity_score']:.4f}")
            print(f"   内容: {result['text']}")
            print(f"   元数据: {result['metadata']}")
            print()

        # 获取统计信息
        stats = manager.get_collection_info()
        print(f"\n知识库统计: {stats}")

    except Exception as e:
        print(f"❌ 演示失败: {e}")


if __name__ == "__main__":
    main()
