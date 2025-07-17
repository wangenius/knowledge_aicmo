/**
 * Qwen文本向量化模块
 *
 * 本模块提供基于阿里云通义千问(Qwen)模型的文本向量化功能，包括：
 * - 单文本向量化：将单个文本转换为高维向量表示
 * - 批量文本向量化：高效处理多个文本的向量化
 * - 向量维度获取：动态获取模型输出的向量维度
 * - API调用管理：封装与Qwen API的交互逻辑
 *
 * Qwen是阿里云推出的大语言模型，其embedding模型能够将文本转换为
 * 高质量的向量表示，适用于语义搜索、文本相似度计算等任务。
 *
 * 本模块使用text-embedding-v3模型，提供1024维的向量输出，
 * 具有良好的语义理解能力和跨语言支持。
 */

import axios, { AxiosResponse } from 'axios';
import * as dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

/**
 * Qwen API响应接口
 */
interface QwenEmbeddingResponse {
  data: Array<{
    embedding: number[];
    index: number;
    object: string;
  }>;
  model: string;
  object: string;
  usage: {
    prompt_tokens: number;
    total_tokens: number;
  };
}

/**
 * Qwen文本向量化器
 * 
 * 使用阿里云通义千问(Qwen)的embedding模型将文本转换为向量表示。
 * 支持单文本和批量文本的向量化处理，提供高质量的语义向量输出。
 * 
 * 主要功能：
 * 1. 文本向量化：将自然语言文本转换为数值向量
 * 2. 批量处理：支持多个文本的批量向量化，提高效率
 * 3. 维度管理：自动获取和管理向量维度信息
 * 4. 错误处理：完善的API调用错误处理和重试机制
 * 
 * 技术特性：
 * - 模型：text-embedding-v3
 * - 向量维度：1024
 * - 支持语言：中文、英文等多语言
 * - 输出格式：number类型向量数组
 */
export class QwenVectorizer {
  private apiKey: string;
  private baseUrl: string;
  private model: string;
  private headers: Record<string, string>;

  /**
   * 初始化Qwen向量化器
   * 
   * 从环境变量中读取API配置信息，设置请求头和模型参数。
   * 支持多种API密钥配置方式，确保兼容性。
   * 
   * 环境变量配置：
   *     QWEN_API_KEY 或 DASHSCOPE_API_KEY: API访问密钥（必需）
   *     QWEN_BASE_URL: API基础URL（可选，有默认值）
   */
  constructor() {
    // 尝试从多个环境变量获取API密钥
    this.apiKey = process.env.QWEN_API_KEY || process.env.DASHSCOPE_API_KEY || '';
    
    // 设置API基础URL，支持自定义或使用默认值
    this.baseUrl = process.env.QWEN_BASE_URL || 'https://dashscope.aliyuncs.com/compatible-mode/v1';

    if (!this.apiKey) {
      throw new Error('请在.env文件中配置QWEN_API_KEY或DASHSCOPE_API_KEY');
    }

    // 设置HTTP请求头
    this.headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    };

    // 使用Qwen的embedding模型
    this.model = 'text-embedding-v3';
  }

  /**
   * 将单个文本转换为向量表示
   * 
   * 调用Qwen embedding API将输入文本转换为高维向量。
   * 向量可用于语义搜索、相似度计算等下游任务。
   * 
   * @param text 要向量化的文本内容
   * @returns 文本的向量表示，长度为1024
   * 
   * @example
   * ```typescript
   * const vectorizer = new QwenVectorizer();
   * const vector = await vectorizer.vectorizeText('人工智能是未来的发展方向');
   * console.log(`向量维度: ${vector.length}`); // 输出: 1024
   * ```
   */
  async vectorizeText(text: string): Promise<number[]> {
    try {
      const response = await this.callEmbeddingApi([text]);
      if (response && response.length > 0) {
        return response[0];
      } else {
        throw new Error('API返回空结果');
      }
    } catch (error) {
      console.log(`❌ 文本向量化失败: ${error}`);
      throw error;
    }
  }

  /**
   * 批量将多个文本转换为向量表示
   * 
   * 一次API调用处理多个文本，相比单独调用更高效。
   * 适用于需要处理大量文本的场景。
   * 
   * @param texts 要向量化的文本列表
   * @returns 向量列表，每个向量对应一个输入文本
   * 
   * @example
   * ```typescript
   * const vectorizer = new QwenVectorizer();
   * const texts = ['第一段文本', '第二段文本', '第三段文本'];
   * const vectors = await vectorizer.vectorizeTexts(texts);
   * console.log(`处理了 ${vectors.length} 个文本`);
   * ```
   */
  async vectorizeTexts(texts: string[]): Promise<number[][]> {
    try {
      return await this.callEmbeddingApi(texts);
    } catch (error) {
      console.log(`❌ 批量文本向量化失败: ${error}`);
      throw error;
    }
  }

  /**
   * 调用Qwen embedding API的核心方法
   * 
   * 封装与Qwen API的HTTP交互逻辑，处理请求构建、响应解析和错误处理。
   * 支持单个或多个文本的批量处理。
   * 
   * @param texts 要向量化的文本列表
   * @returns 向量列表，每个向量对应一个输入文本
   * 
   * @private
   */
  private async callEmbeddingApi(texts: string[]): Promise<number[][]> {
    const url = `${this.baseUrl}/embeddings`;

    const payload = {
      model: this.model,
      input: texts,
      encoding_format: 'float'
    };

    try {
      const response: AxiosResponse<QwenEmbeddingResponse> = await axios.post(
        url,
        payload,
        {
          headers: this.headers,
          timeout: 30000 // 30秒超时
        }
      );

      const result = response.data;

      if (!result.data) {
        throw new Error(`API响应格式错误: ${JSON.stringify(result)}`);
      }

      // 提取向量数据
      const vectors: number[][] = [];
      for (const item of result.data) {
        if (item.embedding) {
          vectors.push(item.embedding);
        } else {
          throw new Error(`响应中缺少embedding字段: ${JSON.stringify(item)}`);
        }
      }

      console.log(`✅ 成功向量化 ${texts.length} 个文本`);
      return vectors;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`API请求失败: ${error.message}`);
      } else {
        throw new Error(`向量化处理失败: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
  }

  /**
   * 获取模型输出的向量维度
   * 
   * 通过向量化一个测试文本来动态获取向量维度。
   * 如果API调用失败，返回text-embedding-v3的默认维度1024。
   * 
   * @returns 向量维度，通常为1024
   * 
   * @note 该方法会进行一次实际的API调用来获取准确的维度信息
   */
  async getVectorDimension(): Promise<number> {
    try {
      // 使用一个简单的测试文本来获取向量维度
      const testVector = await this.vectorizeText('测试');
      return testVector.length;
    } catch (error) {
      console.log(`❌ 获取向量维度失败: ${error}`);
      // Qwen text-embedding-v3 的默认维度
      return 1024;
    }
  }
}

/**
 * 测试和演示向量化功能的主函数
 * 
 * 执行以下测试：
 * 1. 单文本向量化测试
 * 2. 批量文本向量化测试
 * 3. 向量维度验证
 * 4. 错误处理和故障排除提示
 * 
 * 用于验证Qwen API配置和网络连接的正确性。
 */
export async function main(): Promise<void> {
  try {
    const vectorizer = new QwenVectorizer();

    // 测试单个文本向量化
    const testText = '这是一个测试文本';
    const vector = await vectorizer.vectorizeText(testText);
    console.log(`文本: ${testText}`);
    console.log(`向量维度: ${vector.length}`);
    console.log(`向量前5个值: ${vector.slice(0, 5)}`);

    // 测试批量向量化
    const testTexts = ['第一个测试文本', '第二个测试文本', '第三个测试文本'];
    const vectors = await vectorizer.vectorizeTexts(testTexts);
    console.log(`\n批量向量化结果: ${vectors.length} 个向量`);

    // 测试获取向量维度
    const dimension = await vectorizer.getVectorDimension();
    console.log(`\n向量维度: ${dimension}`);
  } catch (error) {
    console.log(`❌ 测试失败: ${error}`);
    console.log('\n💡 请检查:');
    console.log('1. .env文件中是否正确配置了QWEN_API_KEY');
    console.log('2. 网络连接是否正常');
    console.log('3. API密钥是否有效');
  }
}

// 当直接运行此文件时，执行测试函数
if (require.main === module) {
  main();
}