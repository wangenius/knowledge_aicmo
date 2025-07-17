#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库管理核心模块

本模块是整个知识库系统的核心，整合了文本向量化和向量数据库功能，
提供完整的知识库生命周期管理。主要功能包括：

核心功能：
- 知识存储：文本向量化后存储到向量数据库
- 语义检索：基于向量相似度的智能搜索
- 批量处理：支持大量文本的批量向量化和存储
- 集合管理：自动化的数据库集合创建和维护
- 统计分析：提供知识库使用情况的统计信息

技术架构：
- 向量化层：使用Qwen模型进行文本向量化
- 存储层：使用Zilliz云服务进行向量存储
- 管理层：提供统一的知识库操作接口
- 元数据：支持丰富的文档元数据管理

设计特点：
- 自动化：集合创建、schema管理全自动化
- 容错性：完善的错误处理和恢复机制
- 可扩展：支持不同规模的知识库应用
- 易用性：简洁的API设计，降低使用门槛

Author: Vincent Zhou
Date: 2024
Version: 1.0
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from zilliz import ZillizManager, KnowledgeItem
from vectorizer import QwenVectorizer


class KnowledgeManager:
    """
    知识库管理核心类

    整合向量化和向量数据库功能，提供完整的知识库管理解决方案。
    该类是整个系统的核心，负责协调向量化器和数据库管理器的工作。

    主要职责：
    1. 系统集成：整合QwenVectorizer和ZillizManager
    2. 流程管理：管理从文本输入到向量存储的完整流程
    3. 集合管理：自动创建和维护向量数据库集合
    4. 数据处理：处理文本向量化、存储和检索
    5. 错误处理：提供统一的错误处理和日志记录

    技术特性：
    - 向量维度：自动获取并适配Qwen模型的输出维度
    - 相似度计算：使用余弦相似度进行向量比较
    - 自动ID：支持自动生成文档ID
    - 元数据支持：丰富的文档元数据管理
    - 时间戳：自动记录文档创建时间

    使用示例：
        >>> manager = KnowledgeManager("my_knowledge")
        >>> doc_id = manager.vectorize_and_store("知识内容", {"category": "技术"})
        >>> results = manager.search_similar("相关查询", limit=5)
    """

    def __init__(self, collection_name: str = "knowledge_base"):
        """
        初始化知识库管理器

        创建向量化器和数据库管理器实例，获取向量维度信息，
        并确保指定的集合存在且配置正确。

        Args:
            collection_name (str, optional): 集合名称，默认为"knowledge_base"

        Raises:
            Exception: 当向量化器或数据库连接初始化失败时抛出

        Note:
            - 自动获取Qwen模型的向量维度
            - 如果集合不存在会自动创建
            - 如果集合已存在会重新创建以确保schema正确
        """
        self.collection_name = collection_name

        # 初始化向量化器和数据库管理器
        self.vectorizer = QwenVectorizer()
        self.zilliz = ZillizManager()

        # 获取向量维度，用于创建集合schema
        self.vector_dim = self.vectorizer.get_vector_dimension()

        # 确保集合存在且配置正确
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """
        确保集合存在且配置正确

        检查指定的集合是否存在，如果不存在则创建新集合。
        Raises:
            Exception: 当集合操作失败时抛出
        """
        try:
            collections = self.zilliz.list_collections()
            if self.collection_name not in collections:
                self._create_collection()
                print(f"✅ 创建集合 '{self.collection_name}' 成功")
        except Exception as e:
            print(f"❌ 检查/创建集合失败: {e}")
            raise

    def _create_collection(self):
        """
        创建向量数据库集合

        使用ZillizManager的create_collection方法创建带有预定义schema的集合。
        这确保了集合具有固定的字段结构，而不是动态schema。

        集合配置：
        - 维度：根据Qwen模型自动获取
        - Schema：使用预定义的固定字段结构
        - 度量类型：COSINE（余弦相似度）
        - 主键：自动生成ID

        Raises:
            Exception: 当集合创建失败时抛出
        """
        try:
            # 使用ZillizManager的create_collection方法创建带schema的集合
            success = self.zilliz.create_collection(
                collection_name=self.collection_name,
                vector_dim=self.vector_dim,
                description=f"知识库集合 - {self.collection_name}",
            )
            if not success:
                raise Exception("集合创建失败")
        except Exception as e:
            print(f"❌ 创建集合失败: {e}")
            raise

    def vectorize_and_store(self, text: str, metadata: KnowledgeItem) -> str:
        """
        向量化文本并存储到向量数据库
        这是知识库系统的核心功能之一，将输入的文本转换为向量表示
        并存储到Zilliz向量数据库中，同时保存原始文本和元数据。

        处理流程：
        1. 使用Qwen模型将文本向量化
        2. 构建包含向量、文本和元数据的数据记录
        3. 添加时间戳信息
        4. 存储到指定的向量数据库集合

        Args:
            text (str): 要向量化和存储的文本内容
            metadata (Optional[Dict[str, Any]], optional): 可选的元数据信息，
                用于标记文本的分类、来源、标签等附加信息

        Returns:
            str: 存储成功后返回的文档ID（临时生成的UUID）

        Raises:
            Exception: 当向量化或存储过程失败时抛出

        Example:
            >>> manager = KnowledgeManager()
            >>> doc_id = manager.vectorize_and_store(
            ...     "Python是一种编程语言",
            ...     {"category": "技术", "language": "Python"}
            ... )
            >>> print(f"文档已存储，ID: {doc_id}")
        """
        try:
            # 向量化文本
            print(f"🔄 正在向量化文本: {text[:50]}...")
            vector = self.vectorizer.vectorize_text(text)

            if metadata:
                metadata.update(
                    {
                        "vector": vector,
                        "text": text,
                    }
                )

            # 存储到向量数据库
            success = self.zilliz.insert_data(
                self.collection_name, [metadata], self.vector_dim
            )

            if success:
                # 生成临时ID用于返回（实际ID由Zilliz自动生成）
                doc_id = str(uuid.uuid4())
                print(f"✅ 文档存储成功，临时ID: {doc_id}")
                return doc_id
            else:
                raise Exception("数据存储失败")

        except Exception as e:
            print(f"❌ 向量化和存储失败: {e}")
            raise

    def search_similar(
        self, query_text: str, limit: int = 5, score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        基于语义相似度检索相关文本

        这是知识库系统的另一个核心功能，通过向量相似度计算
        找到与查询文本语义最相关的知识条目。

        检索流程：
        1. 将查询文本向量化
        2. 在向量数据库中执行相似度搜索
        3. 根据相似度阈值过滤结果
        4. 格式化并返回检索结果

        Args:
            query_text (str): 查询文本，用于搜索相关知识
            limit (int, optional): 返回结果的最大数量，默认为5
            score_threshold (float, optional): 相似度阈值，低于此值的结果
                将被过滤掉，默认为0.0（不过滤）

        Returns:
            List[Dict[str, Any]]: 检索结果列表，每个结果包含：
                - id: 文档ID
                - text: 原始文本内容
                - metadata: 元数据信息
                - created_at: 创建时间
                - similarity_score: 相似度分数（0-1之间）

        Example:
            >>> manager = KnowledgeManager()
            >>> results = manager.search_similar(
            ...     "什么是机器学习？",
            ...     limit=3,
            ...     score_threshold=0.5
            ... )
            >>> for result in results:
            ...     print(f"相似度: {result['similarity_score']:.3f}")
            ...     print(f"内容: {result['text'][:50]}...")
        """
        try:
            # 向量化查询文本
            print(f"🔄 正在向量化查询文本: {query_text[:50]}...")
            query_vector = self.vectorizer.vectorize_text(query_text)

            # 在向量数据库中搜索
            results = self.zilliz.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                output_fields=[
                    "text",
                    "topic",
                    "weight",
                    "created_at",
                    "title",
                    "tags",
                ],
            )

            # 过滤结果并格式化
            filtered_results = []
            for result in results:
                if result.get("distance", 0) >= score_threshold:
                    # 重新构建metadata格式以保持兼容性
                    metadata = {
                        "topic": result.get("topic", ""),
                        "weight": result.get("weight", 1.0),
                        "title": result.get("title", ""),
                        "tags": result.get("tags", []),
                    }
                    filtered_results.append(
                        {
                            "id": result.get("id", "auto_generated"),
                            "text": result.get("text"),
                            "metadata": metadata,
                            "created_at": result.get("created_at"),
                            "similarity_score": result.get("distance", 0),
                        }
                    )

            print(f"✅ 检索完成，找到 {len(filtered_results)} 条相关结果")
            return filtered_results

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        获取当前知识库集合的详细信息

        提供知识库的统计信息和配置详情，用于监控和管理。

        Returns:
            Dict[str, Any]: 集合信息字典，包含：
                - collection_name: 集合名称
                - vector_dimension: 向量维度
                - stats: 统计信息（记录数量等）

        Example:
            >>> manager = KnowledgeManager()
            >>> info = manager.get_collection_info()
            >>> print(f"集合: {info['collection_name']}")
            >>> print(f"维度: {info['vector_dimension']}")
            >>> print(f"记录数: {info['stats'].get('row_count', 0)}")
        """
        try:
            stats = self.zilliz.get_collection_stats(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vector_dimension": self.vector_dim,
                "stats": stats,
            }
        except Exception as e:
            print(f"❌ 获取集合信息失败: {e}")
            return {}


def main():
    pass


if __name__ == "__main__":
    main()
