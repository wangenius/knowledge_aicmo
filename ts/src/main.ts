import { KnowledgeManager } from './knowledgeManager';

/**
 * 主函数 - 用法演示
 */
async function main(): Promise<void> {
  try {
    console.log('=== 知识库用法演示 ===');

    // 方式1：使用类接口
    console.log('\n1. 使用类接口:');
    const manager = new KnowledgeManager('demo_knowledge');

    // 等待初始化完成
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 批量存储知识
    const docIds = await manager.vectorizeAndStore(
      '我的公司叫letus twinkle',
      {
        topic: '内容',
        weight: 2,
        title: '标题',
        tags: ['标签'],
      }
    );
    console.log(`存储完成，文档IDs: ${docIds}`);

    // 检索知识
    const query = '我叫什么';
    const results = await manager.searchSimilar(query, 2);

    console.log(`\n查询: ${query}`);
    console.log('检索结果:');
    results.forEach((result, index) => {
      console.log(`${index + 1}. 相似度: ${result.similarity_score.toFixed(4)}`);
      console.log(`   内容: ${result.text}`);
      console.log(`   元数据: ${JSON.stringify(result.metadata)}`);
      console.log();
    });

    // 获取统计信息
    const stats = await manager.getCollectionInfo();
    console.log(`\n知识库统计: ${JSON.stringify(stats, null, 2)}`);
  } catch (error) {
    console.log(`❌ 演示失败: ${error}`);
  }
}

// 当直接运行此文件时，执行主函数
if (require.main === module) {
  main();
}

export { main };