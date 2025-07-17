/**
 * 知识库管理核心模块
 *
 * 本模块是整个知识库系统的核心，整合了文本向量化和向量数据库功能，
 * 提供完整的知识库生命周期管理。主要功能包括：
 *
 * 核心功能：
 * - 知识存储：文本向量化后存储到向量数据库
 * - 语义检索：基于向量相似度的智能搜索
 * - 批量处理：支持大量文本的批量向量化和存储
 * - 集合管理：自动化的数据库集合创建和维护
 * - 统计分析：提供知识库使用情况的统计信息
 *
 * 技术架构：
 * - 向量化层：使用Qwen模型进行文本向量化
 * - 存储层：使用Zilliz云服务进行向量存储
 * - 管理层：提供统一的知识库操作接口
 * - 元数据：支持丰富的文档元数据管理
 *
 * 设计特点：
 * - 自动化：集合创建、schema管理全自动化
 * - 容错性：完善的错误处理和恢复机制
 * - 可扩展：支持不同规模的知识库应用
 * - 易用性：简洁的API设计，降低使用门槛
 *
 * Author: Vincent Zhou
 * Date: 2024
 * Version: 1.0
 */

import { v4 as uuidv4 } from 'uuid';
import { ZillizManager, KnowledgeItem, SearchResult } from './zilliz';
import { QwenVectorizer } from './vectorizer';

/**
 * 搜索结果接口
 */
export interface KnowledgeSearchResult {
  id: string | number;
  text: string;
  metadata: {
    topic: string;
    weight: number;
    title: string;
    tags: string[];
  };
  created_at: number;
  similarity_score: number;
}

/**
 * 集合信息接口
 */
export interface CollectionInfo {
  collection_name: string;
  vector_dimension: number;
  stats: Record<string, any>;
}

/**
 * 知识库管理核心类
 *
 * 整合向量化和向量数据库功能，提供完整的知识库管理解决方案。
 * 该类是整个系统的核心，负责协调向量化器和数据库管理器的工作。
 *
 * 主要职责：
 * 1. 系统集成：整合QwenVectorizer和ZillizManager
 * 2. 流程管理：管理从文本输入到向量存储的完整流程
 * 3. 集合管理：自动创建和维护向量数据库集合
 * 4. 数据处理：处理文本向量化、存储和检索
 * 5. 错误处理：提供统一的错误处理和日志记录
 *
 * 技术特性：
 * - 向量维度：自动获取并适配Qwen模型的输出维度
 * - 相似度计算：使用余弦相似度进行向量比较
 * - 自动ID：支持自动生成文档ID
 * - 元数据支持：丰富的文档元数据管理
 * - 时间戳：自动记录文档创建时间
 *
 * 使用示例：
 * ```typescript
 * const manager = new KnowledgeManager('my_knowledge');
 * const docId = await manager.vectorizeAndStore('知识内容', {topic: '技术', weight: 1.0, title: '标题', tags: ['标签']});
 * const results = await manager.searchSimilar('相关查询', 5);
 * ```
 */
export class KnowledgeManager {
  private collectionName: string;
  private vectorizer: QwenVectorizer;
  private zilliz: ZillizManager;
  private vectorDim: number = 1024;

  /**
   * 初始化知识库管理器
   *
   * 创建向量化器和数据库管理器实例，获取向量维度信息，
   * 并确保指定的集合存在且配置正确。
   *
   * @param collectionName 集合名称，默认为"knowledge_base"
   */
  constructor(collectionName: string = 'knowledge_base') {
    this.collectionName = collectionName;

    // 初始化向量化器和数据库管理器
    this.vectorizer = new QwenVectorizer();
    this.zilliz = new ZillizManager();

    // 初始化时获取向量维度并确保集合存在
    this.initialize();
  }

  /**
   * 异步初始化方法
   * 
   * 获取向量维度，用于创建集合schema，并确保集合存在且配置正确
   */
  private async initialize(): Promise<void> {
    try {
      // 获取向量维度，用于创建集合schema
      this.vectorDim = await this.vectorizer.getVectorDimension();
      
      // 确保集合存在且配置正确
      await this.ensureCollectionExists();
    } catch (error) {
      console.log(`❌ 初始化失败: ${error}`);
      throw error;
    }
  }

  /**
   * 确保集合存在且配置正确
   *
   * 检查指定的集合是否存在，如果不存在则创建新集合。
   */
  private async ensureCollectionExists(): Promise<void> {
    try {
      const collections = await this.zilliz.listCollections();
      if (!collections.includes(this.collectionName)) {
        await this.createCollection();
        console.log(`✅ 创建集合 '${this.collectionName}' 成功`);
      }
    } catch (error) {
      console.log(`❌ 检查/创建集合失败: ${error}`);
      throw error;
    }
  }

  /**
   * 创建向量数据库集合
   *
   * 使用ZillizManager的createCollection方法创建带有预定义schema的集合。
   * 这确保了集合具有固定的字段结构，而不是动态schema。
   *
   * 集合配置：
   * - 维度：根据Qwen模型自动获取
   * - Schema：使用预定义的固定字段结构
   * - 度量类型：COSINE（余弦相似度）
   * - 主键：自动生成ID
   */
  private async createCollection(): Promise<void> {
    try {
      // 使用ZillizManager的createCollection方法创建带schema的集合
      const success = await this.zilliz.createCollection(
        this.collectionName,
        this.vectorDim,
        `知识库集合 - ${this.collectionName}`
      );
      if (!success) {
        throw new Error('集合创建失败');
      }
    } catch (error) {
      console.log(`❌ 创建集合失败: ${error}`);
      throw error;
    }
  }

  /**
   * 向量化文本并存储到向量数据库
   * 这是知识库系统的核心功能之一，将输入的文本转换为向量表示
   * 并存储到Zilliz向量数据库中，同时保存原始文本和元数据。
   *
   * 处理流程：
   * 1. 使用Qwen模型将文本向量化
   * 2. 构建包含向量、文本和元数据的数据记录
   * 3. 添加时间戳信息
   * 4. 存储到指定的向量数据库集合
   *
   * @param text 要向量化和存储的文本内容
   * @param metadata 可选的元数据信息，用于标记文本的分类、来源、标签等附加信息
   * @returns 存储成功后返回的文档ID（临时生成的UUID）
   *
   * @example
   * ```typescript
   * const manager = new KnowledgeManager();
   * const docId = await manager.vectorizeAndStore(
   *   'Python是一种编程语言',
   *   {topic: '技术', weight: 1.0, title: 'Python介绍', tags: ['编程', 'Python']}
   * );
   * console.log(`文档已存储，ID: ${docId}`);
   * ```
   */
  async vectorizeAndStore(
    text: string,
    metadata: {
      topic: string;
      weight: number;
      title: string;
      tags: string[];
    }
  ): Promise<string> {
    try {
      // 向量化文本
      console.log(`🔄 正在向量化文本: ${text.substring(0, 50)}...`);
      const vector = await this.vectorizer.vectorizeText(text);

      // 构建知识库数据项
      const knowledgeItem: KnowledgeItem = {
        vector,
        text,
        topic: metadata.topic,
        weight: metadata.weight,
        title: metadata.title,
        tags: metadata.tags,
        created_at: Math.floor(Date.now() / 1000) // Unix时间戳
      };

      // 存储到向量数据库
      const success = await this.zilliz.insertData(
        this.collectionName,
        [knowledgeItem],
        this.vectorDim
      );

      if (success) {
        // 生成临时ID用于返回（实际ID由Zilliz自动生成）
        const docId = uuidv4();
        console.log(`✅ 文档存储成功，临时ID: ${docId}`);
        return docId;
      } else {
        throw new Error('数据存储失败');
      }
    } catch (error) {
      console.log(`❌ 向量化和存储失败: ${error}`);
      throw error;
    }
  }

  /**
   * 基于语义相似度检索相关文本
   *
   * 这是知识库系统的另一个核心功能，通过向量相似度计算
   * 找到与查询文本语义最相关的知识条目。
   *
   * 检索流程：
   * 1. 将查询文本向量化
   * 2. 在向量数据库中执行相似度搜索
   * 3. 根据相似度阈值过滤结果
   * 4. 格式化并返回检索结果
   *
   * @param queryText 查询文本，用于搜索相关知识
   * @param limit 返回结果的最大数量，默认为5
   * @param scoreThreshold 相似度阈值，低于此值的结果将被过滤掉，默认为0.0（不过滤）
   * @returns 检索结果列表，每个结果包含id、text、metadata、created_at、similarity_score
   *
   * @example
   * ```typescript
   * const manager = new KnowledgeManager();
   * const results = await manager.searchSimilar(
   *   '什么是机器学习？',
   *   3,
   *   0.5
   * );
   * for (const result of results) {
   *   console.log(`相似度: ${result.similarity_score.toFixed(3)}`);
   *   console.log(`内容: ${result.text.substring(0, 50)}...`);
   * }
   * ```
   */
  async searchSimilar(
    queryText: string,
    limit: number = 5,
    scoreThreshold: number = 0.0
  ): Promise<KnowledgeSearchResult[]> {
    try {
      // 向量化查询文本
      console.log(`🔄 正在向量化查询文本: ${queryText.substring(0, 50)}...`);
      const queryVector = await this.vectorizer.vectorizeText(queryText);

      // 在向量数据库中搜索
      const results = await this.zilliz.search(
        this.collectionName,
        queryVector,
        limit,
        ['text', 'topic', 'weight', 'created_at', 'title', 'tags']
      );

      // 过滤结果并格式化
      const filteredResults: KnowledgeSearchResult[] = [];
      for (const result of results) {
        if ((result.distance || 0) >= scoreThreshold) {
          // 重新构建metadata格式以保持兼容性
          const metadata = {
            topic: result.topic || '',
            weight: result.weight || 1.0,
            title: result.title || '',
            tags: result.tags || []
          };
          
          filteredResults.push({
            id: result.id || 'auto_generated',
            text: result.text || '',
            metadata,
            created_at: result.created_at || 0,
            similarity_score: result.distance || 0
          });
        }
      }

      console.log(`✅ 检索完成，找到 ${filteredResults.length} 条相关结果`);
      return filteredResults;
    } catch (error) {
      console.log(`❌ 检索失败: ${error}`);
      throw error;
    }
  }

  /**
   * 获取当前知识库集合的详细信息
   *
   * 提供知识库的统计信息和配置详情，用于监控和管理。
   *
   * @returns 集合信息字典，包含collection_name、vector_dimension、stats
   *
   * @example
   * ```typescript
   * const manager = new KnowledgeManager();
   * const info = await manager.getCollectionInfo();
   * console.log(`集合: ${info.collection_name}`);
   * console.log(`维度: ${info.vector_dimension}`);
   * console.log(`记录数: ${info.stats.row_count || 0}`);
   * ```
   */
  async getCollectionInfo(): Promise<CollectionInfo> {
    try {
      const stats = await this.zilliz.getCollectionStats(this.collectionName);
      return {
        collection_name: this.collectionName,
        vector_dimension: this.vectorDim,
        stats
      };
    } catch (error) {
      console.log(`❌ 获取集合信息失败: ${error}`);
      return {
        collection_name: this.collectionName,
        vector_dimension: this.vectorDim,
        stats: {}
      };
    }
  }

  /**
   * 批量向量化并存储多个文本
   *
   * 高效处理大量文本的向量化和存储操作。
   *
   * @param texts 要处理的文本数组
   * @param metadatas 对应的元数据数组
   * @returns 存储成功的文档ID数组
   */
  async batchVectorizeAndStore(
    texts: string[],
    metadatas: Array<{
      topic: string;
      weight: number;
      title: string;
      tags: string[];
    }>
  ): Promise<string[]> {
    if (texts.length !== metadatas.length) {
      throw new Error('文本数组和元数据数组长度不匹配');
    }

    try {
      console.log(`🔄 正在批量向量化 ${texts.length} 个文本...`);
      const vectors = await this.vectorizer.vectorizeTexts(texts);

      // 构建知识库数据项数组
      const knowledgeItems: KnowledgeItem[] = texts.map((text, index) => ({
        vector: vectors[index],
        text,
        topic: metadatas[index].topic,
        weight: metadatas[index].weight,
        title: metadatas[index].title,
        tags: metadatas[index].tags,
        created_at: Math.floor(Date.now() / 1000)
      }));

      // 批量存储到向量数据库
      const success = await this.zilliz.insertData(
        this.collectionName,
        knowledgeItems,
        this.vectorDim
      );

      if (success) {
        // 生成临时ID数组用于返回
        const docIds = texts.map(() => uuidv4());
        console.log(`✅ 批量存储成功，处理了 ${texts.length} 个文档`);
        return docIds;
      } else {
        throw new Error('批量数据存储失败');
      }
    } catch (error) {
      console.log(`❌ 批量向量化和存储失败: ${error}`);
      throw error;
    }
  }
}

/**
 * 主函数，用于测试和演示
 */
export async function main(): Promise<void> {
  // 这里可以添加测试代码
  console.log('KnowledgeManager 模块已加载');
}

// 当直接运行此文件时，执行测试函数
if (require.main === module) {
  main();
}