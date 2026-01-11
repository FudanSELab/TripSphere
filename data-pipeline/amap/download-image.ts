import * as fs from 'fs';
import * as path from 'path';
import lodash from 'lodash';

// 配置
const QPS = 2; // 每秒2个请求
const REQUEST_INTERVAL = 1000 / QPS; // 500ms
const BATCH_SIZE = 5; // 每次并行处理的POI数量

// 日志文件路径
const LOG_FILE = 'amap.log';
// JSON结果文件
const MERGED_JSON_FILE = './json-results-merge.json';
// 图片保存目录
const IMAGE_DIR = './image-results';

// 确保目录存在
if (!fs.existsSync(IMAGE_DIR)) {
    fs.mkdirSync(IMAGE_DIR, { recursive: true });
}

/**
 * 写入日志
 */
function log(message: string) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    fs.appendFileSync(LOG_FILE, logMessage);
    console.log(logMessage.trim());
}

/**
 * 延迟函数
 */
function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 下载图片
 */
async function downloadImage(url: string, savePath: string): Promise<void> {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const arrayBuffer = await response.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        
        // 从Content-Type获取文件扩展名，如果没有则默认使用jpg
        const contentType = response.headers.get('content-type') || '';
        let ext = '.jpg';
        if (contentType.includes('png')) {
            ext = '.png';
        } else if (contentType.includes('gif')) {
            ext = '.gif';
        } else if (contentType.includes('webp')) {
            ext = '.webp';
        } else if (contentType.includes('jpeg')) {
            ext = '.jpg';
        }
        
        const filepath = `${savePath}${ext}`;
        fs.writeFileSync(filepath, buffer);
        log(`下载图片: ${filepath}`);
    } catch (error) {
        log(`下载图片失败 ${url}: ${error instanceof Error ? error.message : String(error)}`);
        throw error;
    }
}

/**
 * 下载POI的所有图片（并行下载）
 */
async function downloadPOIPhotos(poi: { id?: string; photos?: Array<{ title?: string; url?: string }> }): Promise<void> {
    if (!poi.id || !poi.photos || poi.photos.length === 0) {
        return;
    }
    
    const poiId = poi.id;
    const dirPath = path.join(IMAGE_DIR, poiId);
    
    // 确保目录存在
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
    
    // 构建所有下载任务
    const downloadTasks = poi.photos
        .map((photo, index) => {
            if (!photo.url) {
                return null;
            }
            const savePath = path.join(dirPath, `${index}`);
            return downloadImage(photo.url, savePath).catch(error => {
                // 下载失败记录日志但继续处理其他图片
                log(`跳过图片下载: ${poiId}/${index}`);
            });
        })
        .filter((task): task is Promise<void> => task !== null);
    
    // 并行执行所有下载任务
    await Promise.all(downloadTasks);
}

/**
 * 批量处理POI数组，每次并行处理指定数量的POI
 */
async function processPOIsInBatches(pois: Array<{ id?: string; photos?: Array<{ title?: string; url?: string }> }>): Promise<void> {
    const total = pois.length;
    log(`开始处理 ${total} 个POI，每批 ${BATCH_SIZE} 个`);

    const chunks = lodash.chunk(pois, BATCH_SIZE);
    const totalBatches = chunks.length;
    
    for (let i = 0; i < chunks.length; i++) {
        const batch = chunks[i];
        const batchNumber = i + 1;
        const startIndex = i * BATCH_SIZE + 1;
        const endIndex = Math.min((i + 1) * BATCH_SIZE, total);
        
        log(`处理批次 ${batchNumber}/${totalBatches} (POI ${startIndex}-${endIndex})`);
        
        // 并行处理当前批次的所有POI
        await Promise.all(batch.map(poi => downloadPOIPhotos(poi)));
        
        // 批次之间的延迟，避免请求过快
        if (i < chunks.length - 1) {
            await delay(REQUEST_INTERVAL);
        }
    }
    
    log(`完成处理所有 ${total} 个POI`);
}

/**
 * 主函数：下载所有图片
 */
async function main() {
    log('=== 开始图片下载任务 ===');
    
    // 检查文件是否存在
    if (!fs.existsSync(MERGED_JSON_FILE)) {
        log(`错误: 文件 ${MERGED_JSON_FILE} 不存在`);
        process.exit(1);
    }
    
    try {
        // 读取合并后的JSON文件
        log(`读取文件: ${MERGED_JSON_FILE}`);
        const fileContent = fs.readFileSync(MERGED_JSON_FILE, 'utf-8');
        const pois: Array<{ id?: string; photos?: Array<{ title?: string; url?: string }> }> = JSON.parse(fileContent);
        
        if (!Array.isArray(pois)) {
            log(`错误: 文件 ${MERGED_JSON_FILE} 不是一个数组`);
            process.exit(1);
        }
        
        if (pois.length === 0) {
            log(`警告: 文件 ${MERGED_JSON_FILE} 中没有POI数据`);
            process.exit(0);
        }
        
        log(`文件包含 ${pois.length} 个POI`);
        
        // 批量处理POI
        await processPOIsInBatches(pois);
        
        log('=== 图片下载任务完成 ===');
    } catch (error) {
        log(`处理文件失败 ${MERGED_JSON_FILE}: ${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    }
}

// 运行主函数
main().catch(error => {
    log(`致命错误: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
});
