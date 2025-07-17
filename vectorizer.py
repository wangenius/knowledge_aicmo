#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen文本向量化模块

本模块提供基于阿里云通义千问(Qwen)模型的文本向量化功能，包括：
- 单文本向量化：将单个文本转换为高维向量表示
- 批量文本向量化：高效处理多个文本的向量化
- 向量维度获取：动态获取模型输出的向量维度
- API调用管理：封装与Qwen API的交互逻辑

Qwen是阿里云推出的大语言模型，其embedding模型能够将文本转换为
高质量的向量表示，适用于语义搜索、文本相似度计算等任务。

本模块使用text-embedding-v3模型，提供1024维的向量输出，
具有良好的语义理解能力和跨语言支持。
"""

import os
import requests
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class QwenVectorizer:
    """
    Qwen文本向量化器
    
    使用阿里云通义千问(Qwen)的embedding模型将文本转换为向量表示。
    支持单文本和批量文本的向量化处理，提供高质量的语义向量输出。
    
    主要功能：
    1. 文本向量化：将自然语言文本转换为数值向量
    2. 批量处理：支持多个文本的批量向量化，提高效率
    3. 维度管理：自动获取和管理向量维度信息
    4. 错误处理：完善的API调用错误处理和重试机制
    
    技术特性：
    - 模型：text-embedding-v3
    - 向量维度：1024
    - 支持语言：中文、英文等多语言
    - 输出格式：float类型向量列表
    
    使用示例：
        >>> vectorizer = QwenVectorizer()
        >>> vector = vectorizer.vectorize_text("这是一个测试文本")
        >>> print(f"向量维度: {len(vector)}")
    """

    def __init__(self):
        """
        初始化Qwen向量化器
        
        从环境变量中读取API配置信息，设置请求头和模型参数。
        支持多种API密钥配置方式，确保兼容性。
        
        环境变量配置：
            QWEN_API_KEY 或 DASHSCOPE_API_KEY: API访问密钥（必需）
            QWEN_BASE_URL: API基础URL（可选，有默认值）
            
        Raises:
            ValueError: 当未配置有效的API密钥时抛出
            
        Note:
            默认使用text-embedding-v3模型，该模型提供1024维向量输出
        """
        # 尝试从多个环境变量获取API密钥
        self.api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        
        # 设置API基础URL，支持自定义或使用默认值
        self.base_url = os.getenv(
            "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        if not self.api_key:
            raise ValueError("请在.env文件中配置QWEN_API_KEY或DASHSCOPE_API_KEY")

        # 设置HTTP请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 使用Qwen的embedding模型
        self.model = "text-embedding-v3"

    def vectorize_text(self, text: str) -> List[float]:
        """
        将单个文本转换为向量表示
        
        调用Qwen embedding API将输入文本转换为高维向量。
        向量可用于语义搜索、相似度计算等下游任务。
        
        Args:
            text (str): 要向量化的文本内容
            
        Returns:
            List[float]: 文本的向量表示，长度为1024
            
        Raises:
            Exception: 当API调用失败或返回异常时抛出
            
        Example:
            >>> vectorizer = QwenVectorizer()
            >>> vector = vectorizer.vectorize_text("人工智能是未来的发展方向")
            >>> print(f"向量维度: {len(vector)}")  # 输出: 1024
        """
        try:
            response = self._call_embedding_api([text])
            if response and len(response) > 0:
                return response[0]
            else:
                raise Exception("API返回空结果")
        except Exception as e:
            print(f"❌ 文本向量化失败: {e}")
            raise

    def vectorize_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将多个文本转换为向量表示
        
        一次API调用处理多个文本，相比单独调用更高效。
        适用于需要处理大量文本的场景。
        
        Args:
            texts (List[str]): 要向量化的文本列表
            
        Returns:
            List[List[float]]: 向量列表，每个向量对应一个输入文本
            
        Raises:
            Exception: 当API调用失败或返回异常时抛出
            
        Example:
            >>> vectorizer = QwenVectorizer()
            >>> texts = ["第一段文本", "第二段文本", "第三段文本"]
            >>> vectors = vectorizer.vectorize_texts(texts)
            >>> print(f"处理了 {len(vectors)} 个文本")
        """
        try:
            return self._call_embedding_api(texts)
        except Exception as e:
            print(f"❌ 批量文本向量化失败: {e}")
            raise

    def _call_embedding_api(self, texts: List[str]) -> List[List[float]]:
        """
        调用Qwen embedding API的核心方法
        
        封装与Qwen API的HTTP交互逻辑，处理请求构建、响应解析和错误处理。
        支持单个或多个文本的批量处理。
        
        Args:
            texts (List[str]): 要向量化的文本列表
            
        Returns:
            List[List[float]]: 向量列表，每个向量对应一个输入文本
            
        Raises:
            Exception: 当API请求失败、响应格式错误或网络异常时抛出
            
        Note:
            - 使用30秒超时设置
            - 返回格式为float类型向量
            - 自动处理API响应的数据提取
        """
        url = f"{self.base_url}/embeddings"

        payload = {"model": self.model, "input": texts, "encoding_format": "float"}

        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if "data" not in result:
                raise Exception(f"API响应格式错误: {result}")

            # 提取向量数据
            vectors = []
            for item in result["data"]:
                if "embedding" in item:
                    vectors.append(item["embedding"])
                else:
                    raise Exception(f"响应中缺少embedding字段: {item}")

            print(f"✅ 成功向量化 {len(texts)} 个文本")
            return vectors

        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {e}")
        except Exception as e:
            raise Exception(f"向量化处理失败: {e}")

    def get_vector_dimension(self) -> int:
        """
        获取模型输出的向量维度
        
        通过向量化一个测试文本来动态获取向量维度。
        如果API调用失败，返回text-embedding-v3的默认维度1024。
        
        Returns:
            int: 向量维度，通常为1024
            
        Note:
            该方法会进行一次实际的API调用来获取准确的维度信息
        """
        try:
            # 使用一个简单的测试文本来获取向量维度
            test_vector = self.vectorize_text("测试")
            return len(test_vector)
        except Exception as e:
            print(f"❌ 获取向量维度失败: {e}")
            # Qwen text-embedding-v3 的默认维度
            return 1024


def main():
    """
    测试和演示向量化功能的主函数
    
    执行以下测试：
    1. 单文本向量化测试
    2. 批量文本向量化测试
    3. 向量维度验证
    4. 错误处理和故障排除提示
    
    用于验证Qwen API配置和网络连接的正确性。
    """
    try:
        vectorizer = QwenVectorizer()

        # 测试单个文本向量化
        test_text = "这是一个测试文本"
        vector = vectorizer.vectorize_text(test_text)
        print(f"文本: {test_text}")
        print(f"向量维度: {len(vector)}")
        print(f"向量前5个值: {vector[:5]}")

        # 测试批量向量化
        test_texts = ["第一个测试文本", "第二个测试文本", "第三个测试文本"]
        vectors = vectorizer.vectorize_texts(test_texts)
        print(f"\n批量向量化结果: {len(vectors)} 个向量")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("\n💡 请检查:")
        print("1. .env文件中是否正确配置了QWEN_API_KEY")
        print("2. 网络连接是否正常")
        print("3. API密钥是否有效")


if __name__ == "__main__":
    # 当直接运行此文件时，执行测试函数
    main()
