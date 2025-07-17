/**
 * Zilliz云向量数据库管理模块
 *
 * 本模块提供Zilliz云服务的完整管理功能，包括：
 * - 多种认证方式的连接管理
 * - 向量数据的插入和存储
 * - 高效的向量相似度搜索
 * - 集合管理和统计信息获取
 *
 * Zilliz是基于Milvus的云原生向量数据库服务，专门用于存储和检索高维向量数据。
 * 本模块封装了与Zilliz云服务交互的所有底层操作，为上层应用提供简洁的接口。
 */

import * as dotenv from 'dotenv';
import axios, { AxiosResponse } from 'axios';

// 加载环境变量
dotenv.config();

// Zilliz RESTful API 响应接口
interface ZillizResponse<T = any> {
  code: number;
  message?: string;
  data?: T;
}

// 集合信息接口
interface CollectionInfo {
  collectionName: string;
  description?: string;
  fields: FieldSchema[];
}

// 字段定义接口
interface FieldSchema {
  fieldName: string;
  dataType: string;
  isPrimary?: boolean;
  elementDataType?: string;
  maxLength?: number;
  dimension?: number;
}

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

/**
 * 搜索结果接口
 */
export interface SearchResult {
  id: string | number;
  distance: number;
  text?: string;
  topic?: string;
  weight?: number;
  created_at?: number;
  title?: string;
  tags?: string[];
}

/**
 * Zilliz云服务管理类 (RESTful API版本)
 *
 * 该类负责管理与Zilliz云向量数据库的所有交互操作，包括连接管理、
 * 数据插入、向量搜索等核心功能。使用 RESTful API 替代 Node.js SDK，
 * 提供更稳定的连接和更好的兼容性。
 */
export class ZillizManager {
  private endpoint: string;
  private token: string;
  private headers: Record<string, string>;

  /**
   * 初始化Zilliz管理器
   *
   * 从环境变量中读取连接配置信息，并设置 RESTful API 客户端。
   * 支持多种认证方式的自动检测和配置。
   */
  constructor() {
    // 从环境变量读取配置信息
    this.endpoint = process.env.ZILLIZ_ENDPOINT || '';
    const token = process.env.ZILLIZ_TOKEN || process.env.ZILLIZ_API_KEY;
    const username = process.env.ZILLIZ_USERNAME;
    const password = process.env.ZILLIZ_PASSWORD;

    if (!this.endpoint) {
      throw new Error('请在.env文件中配置ZILLIZ_ENDPOINT');
    }

    // 设置认证信息
    if (token) {
      this.token = token;
    } else if (username && password) {
      this.token = `${username}:${password}`;
    } else {
      throw new Error('请设置ZILLIZ_TOKEN、ZILLIZ_API_KEY或ZILLIZ_USERNAME+ZILLIZ_PASSWORD');
    }

    // 设置请求头
    this.headers = {
      'Authorization': `Bearer ${this.token}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };

    console.log(`✅ Zilliz RESTful API 客户端初始化完成: ${this.endpoint}`);
  }

  /**
   * 发送 HTTP 请求到 Zilliz API
   *
   * 统一的 API 请求方法，处理认证、错误处理和响应解析。
   * 支持 GET、POST、DELETE 等 HTTP 方法。
   */
  private async request<T = any>(
    path: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any
  ): Promise<T> {
    const url = `${this.endpoint}${path}`;
    
    try {
      const response: AxiosResponse<ZillizResponse<T>> = await axios({
        url,
        method,
        headers: this.headers,
        data: body,
        timeout: 30000 // 30秒超时
      });

      const result = response.data;
      
      if (result.code !== 0 && result.code !== 200) {
        throw new Error(`Zilliz API Error: ${result.message || 'Unknown error'}`);
      }

      return result.data || result as T;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        const statusText = error.response?.statusText;
        const message = error.response?.data?.message || error.message;
        console.error(`❌ API请求失败 [${method} ${path}]: HTTP ${status} ${statusText} - ${message}`);
        throw new Error(`HTTP ${status}: ${message}`);
      } else {
        console.error(`❌ API请求失败 [${method} ${path}]:`, error);
        throw error;
      }
    }
  }

  /**
   * 创建带有预定义schema的集合
   *
   * 为知识库数据创建一个标准化的集合，包含向量字段、文本字段和元数据字段。
   * 使用固定的schema确保数据结构的一致性。
   */
  async createCollection(
    collectionName: string,
    vectorDim: number = 768,
    description: string = '知识库向量集合'
  ): Promise<boolean> {
    try {
      // 检查集合是否已存在
      const collections = await this.listCollections();
      if (collections.includes(collectionName)) {
        console.log(`⚠️ 集合 '${collectionName}' 已存在`);
        return true;
      }

      // 定义字段schema
      const fields: FieldSchema[] = [
        {
          fieldName: 'id',
          dataType: 'Int64',
          isPrimary: true
        },
        {
          fieldName: 'vector',
          dataType: 'FloatVector',
          dimension: vectorDim
        },
        {
          fieldName: 'text',
          dataType: 'VarChar',
          maxLength: 65535
        },
        {
          fieldName: 'topic',
          dataType: 'VarChar',
          maxLength: 500
        },
        {
          fieldName: 'weight',
          dataType: 'Float'
        },
        {
          fieldName: 'created_at',
          dataType: 'Int32'
        },
        {
          fieldName: 'title',
          dataType: 'VarChar',
          maxLength: 100
        },
        {
          fieldName: 'tags',
          dataType: 'Array',
          elementDataType: 'VarChar',
          maxLength: 100
        }
      ];

      // 创建集合
      await this.request('/v2/vectordb/collections/create', 'POST', {
        collectionName: collectionName,
        schema: {
          fields: fields
        },
        indexParams: [{
          fieldName: 'vector',
          indexName: 'vector_index',
          metricType: 'COSINE'
        }]
      });

      console.log(`✅ 成功创建集合 '${collectionName}'，向量维度: ${vectorDim}`);
      return true;
    } catch (error) {
      console.log(`❌ 创建集合失败: ${error}`);
      return false;
    }
  }

  /**
   * 向指定集合插入向量数据
   *
   * 将包含向量和元数据的数据批量插入到Zilliz集合中。
   * 如果集合不存在，会自动创建符合schema的集合。
   */
  async insertData(
    collectionName: string,
    data: KnowledgeItem[],
    vectorDim: number = 768
  ): Promise<boolean> {
    try {
      // 检查集合是否存在，不存在则创建
      const collections = await this.listCollections();
      if (!collections.includes(collectionName)) {
        console.log(`🔄 集合 '${collectionName}' 不存在，正在创建...`);
        if (!(await this.createCollection(collectionName, vectorDim))) {
          return false;
        }
      }

      console.log(`🔄 准备插入 ${data.length} 条数据...`);
      
      await this.request('/v2/vectordb/entities/insert', 'POST', {
        collectionName: collectionName,
        data: data
      });

      // 插入数据后，确保集合被加载到内存中以供后续搜索
      await this.loadCollection(collectionName);

      console.log(`✅ 成功插入 ${data.length} 条数据到集合 '${collectionName}'`);
      return true;
    } catch (error) {
      console.log(`❌ 插入数据失败: ${error}`);
      return false;
    }
  }

  /**
   * 加载集合到内存中
   *
   * 在执行搜索操作前，需要将集合加载到内存中。
   * 这是Milvus/Zilliz的要求，未加载的集合无法进行搜索操作。
   */
  async loadCollection(collectionName: string): Promise<boolean> {
    try {
      // 检查集合是否存在
      const collections = await this.listCollections();
      if (!collections.includes(collectionName)) {
        console.log(`⚠️ 集合 '${collectionName}' 不存在`);
        return false;
      }

      // 加载集合
      await this.request('/v2/vectordb/collections/load', 'POST', {
        collectionName: collectionName
      });
      
      console.log(`✅ 成功加载集合 '${collectionName}' 到内存`);
      return true;
    } catch (error) {
      console.log(`❌ 加载集合失败: ${error}`);
      return false;
    }
  }

  /**
   * 执行向量相似度搜索
   *
   * 在指定集合中搜索与查询向量最相似的数据记录。
   * 使用余弦相似度或其他配置的距离度量进行相似度计算。
   */
  async search(
    collectionName: string,
    queryVector: number[],
    limit: number = 5,
    outputFields?: string[]
  ): Promise<SearchResult[]> {
    try {
      if (!outputFields) {
        outputFields = ['text', 'topic', 'weight', 'created_at', 'title', 'tags'];
      }

      // 确保集合已加载到内存中
      if (!(await this.loadCollection(collectionName))) {
        console.log(`❌ 无法加载集合 '${collectionName}'，搜索终止`);
        return [];
      }

      const results = await this.request('/v2/vectordb/entities/search', 'POST', {
        collectionName: collectionName,
        data: [queryVector],
        annsField: 'vector',
        limit: limit,
        outputFields: outputFields
      });

      const searchResults = results || [];
      const formattedResults: SearchResult[] = searchResults.map((result: any) => ({
        id: result.id,
        distance: result.distance || result.score || 0,
        text: result.text,
        topic: result.topic,
        weight: result.weight,
        created_at: result.created_at,
        title: result.title,
        tags: result.tags
      }));
      console.log(`✅ 搜索完成，返回 ${formattedResults.length} 条结果`);
      return formattedResults;
    } catch (error) {
      console.log(`❌ 搜索失败: ${error}`);
      return [];
    }
  }

  /**
   * 获取当前Zilliz实例中的所有集合列表
   */
  async listCollections(): Promise<string[]> {
    try {
      const collections = await this.request<string[]>('/v2/vectordb/collections/list', 'POST', {});
      console.log(`📋 当前集合列表: ${collections}`);
      return collections || [];
    } catch (error) {
      console.log(`❌ 获取集合列表失败: ${error}`);
      return [];
    }
  }

  /**
   * 获取指定集合的详细统计信息
   *
   * 包括记录数量、索引状态、存储大小等统计数据。
   */
  async getCollectionStats(collectionName: string): Promise<Record<string, any>> {
    try {
      const stats = await this.request('/v2/vectordb/collections/describe', 'POST', {
        collectionName: collectionName
      });
      console.log(`📊 集合 '${collectionName}' 统计信息: ${JSON.stringify(stats)}`);
      return stats || {};
    } catch (error) {
      console.log(`❌ 获取集合统计信息失败: ${error}`);
      return {};
    }
  }

  /**
   * 删除指定的集合
   *
   * 完全删除集合及其所有数据和索引。此操作不可逆，请谨慎使用。
   */
  async dropCollection(collectionName: string): Promise<boolean> {
    try {
      // 检查集合是否存在
      const collections = await this.listCollections();
      if (!collections.includes(collectionName)) {
        console.log(`⚠️ 集合 '${collectionName}' 不存在`);
        return false;
      }

      // 删除集合
      await this.request('/v2/vectordb/collections/drop', 'POST', {
        collectionName: collectionName
      });
      
      console.log(`✅ 成功删除集合 '${collectionName}'`);
      return true;
    } catch (error) {
      console.log(`❌ 删除集合失败: ${error}`);
      return false;
    }
  }
}

/**
 * 测试和演示Zilliz管理器功能的主函数
 *
 * 执行基本的连接测试，验证Zilliz服务的可用性。
 * 可用于调试连接问题和验证配置。
 */
export async function main(): Promise<void> {
  try {
    const zilliz = new ZillizManager();
    await zilliz.listCollections();
  } catch (error) {
    console.log(`❌ 程序执行失败: ${error}`);
    console.log('\n💡 请检查:');
    console.log('1. .env文件是否正确配置');
    console.log('2. Zilliz集群是否正常运行');
    console.log('3. 网络连接是否正常');
  }
}

// 当直接运行此文件时，执行测试函数
if (require.main === module) {
  main();
}