"""
Zilliz云向量数据库管理模块

本模块提供Zilliz云服务的完整管理功能，包括：
- 多种认证方式的连接管理
- 向量数据的插入和存储
- 高效的向量相似度搜索
- 集合管理和统计信息获取

Zilliz是基于Milvus的云原生向量数据库服务，专门用于存储和检索高维向量数据。
本模块封装了与Zilliz云服务交互的所有底层操作，为上层应用提供简洁的接口。
"""

import os
from typing import List, Dict, Any, Optional, TypedDict

from pymilvus import MilvusClient, DataType, CollectionSchema, FieldSchema
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class KnowledgeItem(TypedDict):
    """知识库数据项的类型定义"""
    vector: List[float]  # 向量数据
    text: str  # 文本内容
    topic: str  # 主题分类
    weight: float  # 权重
    title: str  # 标题
    tags: List[str]  # 标签列表
    created_at: int  # 创建时间戳（整数）


class ZillizManager:
    """
    Zilliz云服务管理类

    该类负责管理与Zilliz云向量数据库的所有交互操作，包括连接管理、
    数据插入、向量搜索等核心功能。支持多种认证方式，确保连接的
    灵活性和安全性。

    主要功能：
    1. 自动化连接管理：支持Token、API Key、用户名密码等多种认证方式
    2. Schema管理：自动创建带有预定义schema的集合，确保数据结构一致性
    3. 数据操作：提供向量数据的插入、搜索等操作，自动处理数据格式转换
    4. 集合管理：支持集合的创建、删除、列举和统计信息获取
    5. 错误处理：完善的异常处理和错误提示

    Schema结构：
        - id: 主键字段（自动生成）
        - vector: 向量字段（支持自定义维度）
        - text: 文本内容字段
        - topic: 主题分类字段
        - difficulty: 难度级别字段
        - created_at: 创建时间字段

    使用示例：
        >>> manager = ZillizManager()
        >>> # 创建集合（可选，插入数据时会自动创建）
        >>> manager.create_collection("knowledge_base", vector_dim=768)
        >>> # 插入数据
        >>> data = [{
        ...     "vector": [0.1, 0.2, 0.3],
        ...     "text": "机器学习基础知识",
        ...     "metadata": {"topic": "AI", "difficulty": "初级"},
        ...     "created_at": "2024-01-01T12:00:00"
        ... }]
        >>> manager.insert_data("knowledge_base", data)
        >>> # 搜索相似内容
        >>> results = manager.search("knowledge_base", [0.1, 0.2, 0.3], limit=5)
    """

    def __init__(self):
        """
        初始化Zilliz管理器

        从环境变量中读取连接配置信息，并建立与Zilliz云服务的连接。
        支持多种认证方式的自动检测和连接。

        环境变量配置：
            ZILLIZ_ENDPOINT: Zilliz集群端点URL（必需）
            ZILLIZ_TOKEN: 访问令牌（推荐）
            ZILLIZ_API_KEY: API密钥（备选）
            ZILLIZ_USERNAME: 用户名（与密码配合使用）
            ZILLIZ_PASSWORD: 密码（与用户名配合使用）

        Raises:
            ValueError: 当缺少必需的配置信息时抛出
            Exception: 当连接失败时抛出
        """
        # 从环境变量读取配置信息
        self.endpoint = os.getenv("ZILLIZ_ENDPOINT")
        self.api_key = os.getenv("ZILLIZ_API_KEY")
        self.token = os.getenv("ZILLIZ_TOKEN")
        self.username = os.getenv("ZILLIZ_USERNAME")
        self.password = os.getenv("ZILLIZ_PASSWORD")

        if not self.endpoint:
            raise ValueError("请在.env文件中配置ZILLIZ_ENDPOINT")

        # 初始化客户端连接
        self.client = self._create_client()

    def _create_client(self) -> MilvusClient:
        """
        创建Milvus客户端连接

        尝试使用多种认证方式建立与Zilliz云服务的连接。
        按优先级依次尝试：Token认证 -> API Key认证 -> 用户名密码认证

        Returns:
            MilvusClient: 已连接的Milvus客户端实例

        Raises:
            ValueError: 当没有配置任何有效认证信息时抛出
            Exception: 当所有认证方式都失败时抛出最后一个错误

        Note:
            该方法会自动测试连接有效性，确保返回的客户端可以正常使用
        """
        auth_methods = []

        # 尝试不同的认证方式
        if self.token:
            auth_methods.append(("Token", {"uri": self.endpoint, "token": self.token}))

        if self.api_key:
            auth_methods.append(
                ("API Key", {"uri": self.endpoint, "token": self.api_key})
            )

        if self.username and self.password:
            auth_methods.append(
                (
                    "用户名密码",
                    {
                        "uri": self.endpoint,
                        "user": self.username,
                        "password": self.password,
                    },
                )
            )

        if not auth_methods:
            raise ValueError("请配置有效的认证信息（API Key、用户名密码或Token）")

        # 依次尝试每种认证方式
        last_error = None
        for auth_name, auth_params in auth_methods:
            try:
                print(f"🔄 尝试使用{auth_name}认证...")
                client = MilvusClient(**auth_params)

                # 测试连接是否有效
                client.list_collections()

                print(f"✅ 成功连接到Zilliz: {self.endpoint} (使用{auth_name})")
                return client

            except Exception as e:
                print(f"❌ {auth_name}认证失败: {e}")
                last_error = e
                continue

        # 所有认证方式都失败
        print(f"❌ 所有认证方式都失败，最后一个错误: {last_error}")
        raise last_error or Exception("无法建立连接")

    def create_collection(
        self, 
        collection_name: str, 
        vector_dim: int = 768,
        description: str = "知识库向量集合"
    ) -> bool:
        """
        创建带有预定义schema的集合

        为知识库数据创建一个标准化的集合，包含向量字段、文本字段和元数据字段。
        使用固定的schema确保数据结构的一致性。

        Args:
            collection_name (str): 集合名称
            vector_dim (int, optional): 向量维度，默认768（适用于大多数embedding模型）
            description (str, optional): 集合描述

        Returns:
            bool: 创建成功返回True，失败返回False

        Schema结构:
            - id: 主键字段（自动生成）
            - vector: 向量字段（float类型，指定维度）
            - text: 文本内容字段（varchar类型）
            - topic: 主题字段（varchar类型）
            - weight: 权重字段（int类型）
            - created_at: 创建时间字段（varchar类型）

        Example:
            >>> success = manager.create_collection("knowledge_base", vector_dim=768)
        """
        try:
            # 检查集合是否已存在
            if collection_name in self.client.list_collections():
                print(f"⚠️ 集合 '{collection_name}' 已存在")
                return True

            # 定义字段schema
            fields = [
                FieldSchema(
                    name="id", 
                    dtype=DataType.INT64, 
                    is_primary=True, 
                    auto_id=True,
                    description="主键ID"
                ),
                FieldSchema(
                    name="vector", 
                    dtype=DataType.FLOAT_VECTOR, 
                    dim=vector_dim,
                    description="文本向量表示"
                ),
                FieldSchema(
                    name="text", 
                    dtype=DataType.VARCHAR, 
                    max_length=65535,
                    description="原始文本内容"
                ),
                FieldSchema(
                    name="topic", 
                    dtype=DataType.VARCHAR, 
                    max_length=500,
                    description="主题分类"
                ),
                FieldSchema(
                    name="weight", 
                    dtype=DataType.FLOAT, 
                    max_length=100,
                    description="权重"
                ),
                FieldSchema(
                    name="created_at", 
                    dtype=DataType.INT32, 
                    max_length=100,
                    description="创建时间"
                ),
                FieldSchema(
                    name="title",
                    dtype=DataType.VARCHAR,
                    max_length=100,
                    description="标题"
                ),
                FieldSchema(
                    name="tags",
                    dtype=DataType.ARRAY,
                    element_type=DataType.VARCHAR,
                    max_capacity=10,
                    max_length=100,
                    description="标签"
                ),
            ]

            # 创建集合schema
            schema = CollectionSchema(
                fields=fields, 
                description=description
            )

            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema
            )

            # 创建向量索引以提高搜索性能
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="AUTOINDEX",
                metric_type="COSINE"  # 使用余弦相似度
            )
            
            self.client.create_index(
                collection_name=collection_name,
                index_params=index_params
            )

            print(f"✅ 成功创建集合 '{collection_name}'，向量维度: {vector_dim}")
            return True

        except Exception as e:
            print(f"❌ 创建集合失败: {e}")
            return False

    def insert_data(
        self, 
        collection_name: str, 
        data: List[KnowledgeItem], 
        vector_dim: int = 768
    ) -> bool:
        """
        向指定集合插入向量数据

        将包含向量和元数据的数据批量插入到Zilliz集合中。
        如果集合不存在，会自动创建符合schema的集合。
        数据会被转换为符合预定义schema的格式。

        Args:
            collection_name (str): 目标集合名称
            data (List[KnowledgeItem]): 要插入的知识库数据列表，每个元素为KnowledgeItem类型
            vector_dim (int, optional): 向量维度，默认768

        Returns:
            bool: 插入成功返回True，失败返回False

        Example:
            >>> data: List[KnowledgeItem] = [{
            ...     "vector": [0.1, 0.2, 0.3],
            ...     "text": "机器学习是人工智能的重要分支",
            ...     "topic": "人工智能",
            ...     "weight": 1.0,
            ...     "title": "机器学习基础",
            ...     "tags": ["AI", "机器学习"],
            ...     "created_at": 1704067200
            ... }]
            >>> success = manager.insert_data("knowledge_base", data)
        """
        try:
            # 检查集合是否存在，不存在则创建
            if collection_name not in self.client.list_collections():
                print(f"🔄 集合 '{collection_name}' 不存在，正在创建...")
                if not self.create_collection(collection_name, vector_dim):
                    return False

            print(f"🔄 准备插入 {len(data)} 条数据...")
            # 将TypedDict转换为普通字典以兼容pymilvus
            dict_data = [dict(item) for item in data]
            self.client.insert(collection_name=collection_name, data=dict_data)
            
            # 插入数据后，确保集合被加载到内存中以供后续搜索
            self.load_collection(collection_name)
            
            print(f"✅ 成功插入 {len(data)} 条数据到集合 '{collection_name}'")
            return True

        except Exception as e:
            print(f"❌ 插入数据失败: {e}")
            return False

    def load_collection(self, collection_name: str) -> bool:
        """
        加载集合到内存中

        在执行搜索操作前，需要将集合加载到内存中。
        这是Milvus/Zilliz的要求，未加载的集合无法进行搜索操作。

        Args:
            collection_name (str): 要加载的集合名称

        Returns:
            bool: 加载成功返回True，失败返回False

        Example:
            >>> success = manager.load_collection("knowledge_base")
        """
        try:
            # 检查集合是否存在
            if collection_name not in self.client.list_collections():
                print(f"⚠️ 集合 '{collection_name}' 不存在")
                return False

            # 加载集合
            self.client.load_collection(collection_name)
            print(f"✅ 成功加载集合 '{collection_name}' 到内存")
            return True

        except Exception as e:
            print(f"❌ 加载集合失败: {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        执行向量相似度搜索

        在指定集合中搜索与查询向量最相似的数据记录。
        使用余弦相似度或其他配置的距离度量进行相似度计算。

        Args:
            collection_name (str): 要搜索的集合名称
            query_vector (List[float]): 查询向量
            limit (int, optional): 返回结果的最大数量，默认为5
            output_fields (Optional[List[str]], optional): 要返回的字段列表，
                默认返回["text", "topic", "weight", "created_at", "title", "tags"]

        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含：
                - id: 记录ID
                - distance: 相似度分数
                - 指定的output_fields字段

        Example:
            >>> results = manager.search(
            ...     "knowledge_base",
            ...     [0.1, 0.2, 0.3],
            ...     limit=10,
            ...     output_fields=["text", "topic", "weight", "created_at", "title", "tags"]
            ... )
        """
        try:
            if output_fields is None:
                output_fields = ["text", "topic", "weight", "created_at", "title", "tags"]

            # 确保集合已加载到内存中
            if not self.load_collection(collection_name):
                print(f"❌ 无法加载集合 '{collection_name}'，搜索终止")
                return []

            results = self.client.search(
                collection_name=collection_name,
                data=[query_vector],
                limit=limit,
                output_fields=output_fields,
            )

            print(f"✅ 搜索完成，返回 {len(results[0])} 条结果")
            return results[0]

        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

    def list_collections(self) -> List[str]:
        """
        获取当前Zilliz实例中的所有集合列表

        Returns:
            List[str]: 集合名称列表

        Example:
            >>> collections = manager.list_collections()
            >>> print(f"当前集合: {collections}")
        """
        try:
            collections = self.client.list_collections()
            print(f"📋 当前集合列表: {collections}")
            return collections
        except Exception as e:
            print(f"❌ 获取集合列表失败: {e}")
            return []

    def get_collection_stats(self, collection_name: str) -> Dict:
        """
        获取指定集合的详细统计信息

        包括记录数量、索引状态、存储大小等统计数据。

        Args:
            collection_name (str): 集合名称

        Returns:
            Dict: 集合统计信息字典，包含：
                - row_count: 记录数量
                - 其他统计指标

        Example:
            >>> stats = manager.get_collection_stats("my_collection")
            >>> print(f"记录数量: {stats.get('row_count', 0)}")
        """
        try:
            stats = self.client.get_collection_stats(collection_name)
            print(f"📊 集合 '{collection_name}' 统计信息: {stats}")
            return stats
        except Exception as e:
            print(f"❌ 获取集合统计信息失败: {e}")
            return {}

    def drop_collection(self, collection_name: str) -> bool:
        """
        删除指定的集合

        完全删除集合及其所有数据和索引。此操作不可逆，请谨慎使用。

        Args:
            collection_name (str): 要删除的集合名称

        Returns:
            bool: 删除成功返回True，失败返回False

        Example:
            >>> success = manager.drop_collection("old_collection")
        """
        try:
            # 检查集合是否存在
            if collection_name not in self.client.list_collections():
                print(f"⚠️ 集合 '{collection_name}' 不存在")
                return True

            # 删除集合
            self.client.drop_collection(collection_name)
            print(f"✅ 成功删除集合 '{collection_name}'")
            return True

        except Exception as e:
            print(f"❌ 删除集合失败: {e}")
            return False


def main():
    """
    测试和演示Zilliz管理器功能的主函数

    执行基本的连接测试，验证Zilliz服务的可用性。
    可用于调试连接问题和验证配置。
    """
    try:
        zilliz = ZillizManager()
        zilliz.list_collections()
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        print("\n💡 请检查:")
        print("1. .env文件是否正确配置")
        print("2. Zilliz集群是否正常运行")
        print("3. 网络连接是否正常")


if __name__ == "__main__":
    # 当直接运行此文件时，执行测试函数
    main()
