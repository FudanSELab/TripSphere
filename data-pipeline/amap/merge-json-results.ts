import * as fs from 'fs';
import * as path from 'path';
import { Response } from './types';

// JSON结果目录
const RESULTS_DIR = './json-results';
// 输出文件
const OUTPUT_FILE = './json-results-merge.json';

/**
 * 主函数：合并所有JSON文件
 */
function main() {
    console.log('=== 开始合并 JSON 文件 ===\n');
    
    // 检查目录是否存在
    if (!fs.existsSync(RESULTS_DIR)) {
        console.error(`错误: 目录 ${RESULTS_DIR} 不存在`);
        process.exit(1);
    }
    
    // 读取所有JSON文件
    const files = fs.readdirSync(RESULTS_DIR)
        .filter(file => file.endsWith('.json'))
        .map(file => path.join(RESULTS_DIR, file))
        .sort(); // 排序以确保顺序一致
    
    if (files.length === 0) {
        console.log(`警告: 在 ${RESULTS_DIR} 目录下没有找到JSON文件`);
        process.exit(0);
    }
    
    console.log(`找到 ${files.length} 个JSON文件\n`);
    
    // 合并所有POI数据：从每个JSON文件中提取pois数组，打平为一个大的POI数组
    // 使用Map根据poi.id进行去重
    const poiMap = new Map<string, any>();
    let processedFiles = 0;
    let errorFiles = 0;
    let totalPois = 0;
    let duplicateCount = 0;
    
    for (const file of files) {
        try {
            const fileContent = fs.readFileSync(file, 'utf-8');
            const data: Response = JSON.parse(fileContent);
            
            // 只处理成功的请求
            if (data.status === '1' && data.infocode === '10000' && data.pois) {
                // 提取pois数组并打平到poiMap中（每个元素是一个POI对象）
                const pois = data.pois;
                for (const poi of pois) {
                    if (poi.id) {
                        if (!poiMap.has(poi.id)) {
                            poiMap.set(poi.id, poi);
                        } else {
                            duplicateCount++;
                        }
                        totalPois++;
                    }
                }
                processedFiles++;
            } else {
                console.warn(`跳过文件 ${path.basename(file)}: 状态=${data.status}, 错误码=${data.infocode}`);
                errorFiles++;
            }
        } catch (error) {
            console.error(`解析文件失败 ${path.basename(file)}: ${error instanceof Error ? error.message : String(error)}`);
            errorFiles++;
        }
    }
    
    // 将Map转换为数组
    const allPois = Array.from(poiMap.values());
    
    console.log(`处理完成:`);
    console.log(`  成功处理: ${processedFiles} 个文件`);
    console.log(`  跳过/错误: ${errorFiles} 个文件`);
    console.log(`  总POI数量: ${totalPois}`);
    console.log(`  去重后POI数量: ${allPois.length}`);
    console.log(`  重复POI数量: ${duplicateCount}\n`);
    
    // 写入合并后的文件
    try {
        const outputData = JSON.stringify(allPois, null, 2);
        fs.writeFileSync(OUTPUT_FILE, outputData, 'utf-8');
        console.log(`✓ 合并结果已保存到: ${OUTPUT_FILE}`);
        console.log(`  文件大小: ${(outputData.length / 1024 / 1024).toFixed(2)} MB`);
    } catch (error) {
        console.error(`写入文件失败: ${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    }
    
    console.log('\n=== 合并完成 ===');
}

// 运行主函数
main();
