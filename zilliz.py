import os
from typing import List, Dict, Any, Optional

from pymilvus import MilvusClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ZillizManager:
    """Zilliz云服务管理类"""

    def __init__(self):
        self.endpoint = os.getenv("ZILLIZ_ENDPOINT")
        self.api_key = os.getenv("ZILLIZ_API_KEY")
        self.token = os.getenv("ZILLIZ_TOKEN")
        self.username = os.getenv("ZILLIZ_USERNAME")
        self.password = os.getenv("ZILLIZ_PASSWORD")

        if not self.endpoint:
            raise ValueError("请在.env文件中配置ZILLIZ_ENDPOINT")

        # 初始化客户端
        self.client = self._create_client()

    def _create_client(self) -> MilvusClient:
        """创建Milvus客户端连接"""
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

    def insert_data(self, collection_name: str, data: List[Dict[str, Any]]) -> bool:
        """插入数据"""
        try:
            self.client.insert(collection_name=collection_name, data=data)
            print(f"✅ 成功插入 {len(data)} 条数据到集合 '{collection_name}'")
            return True

        except Exception as e:
            print(f"❌ 插入数据失败: {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        try:
            if output_fields is None:
                output_fields = ["text", "metadata"]

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
        """列出所有集合"""
        try:
            collections = self.client.list_collections()
            print(f"📋 当前集合列表: {collections}")
            return collections
        except Exception as e:
            print(f"❌ 获取集合列表失败: {e}")
            return []

    def get_collection_stats(self, collection_name: str) -> Dict:
        """获取集合统计信息"""
        try:
            stats = self.client.get_collection_stats(collection_name)
            print(f"📊 集合 '{collection_name}' 统计信息: {stats}")
            return stats
        except Exception as e:
            print(f"❌ 获取集合统计信息失败: {e}")
            return {}


def main():
    """主函数"""
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
    main()
