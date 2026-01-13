import * as fs from 'fs';
import * as path from 'path';
import { createHash } from 'crypto';
import { Response, SearchParams } from './types';

// 各区 adcode
const adcodes = [
    '310000',
    '310101',
    '310104',
    '310105',
    '310106',
    '310107',
    '310109',
    '310110',
    '310112',
    '310113',
    '310114',
    '310115',
    '310116',
    '310117',
    '310118',
    '310120',
    '310151',
]

// POI类型码映射
const poiHotel = [
    '100100',
    '100101',
    '100102',
    '100103',
    '100104',
    '100105',
    '100200',
    '100201',
]

const poiAttractions = [
    '110000',
    '110100',
    '110101',
    '110102',
    '110103',
    '110104',
    '110105',
    '110106',
    '110200',
    '110201',
    '110202',
    '110203',
    '110204',
    '110205',
    '110206',
    '110207',
    '110208',
    '110209',
    '110210',
]

const poiSciences = [
    '140000',
    '140100',
    '140200',
    '140300',
    '140400',
    '140500',
    '140600',
    '140700',
    '140800',
]

// 关键词映射
const keywordMap: Record<string, string> = {
    '酒店': '酒店',
    '景点': '景点',
    '140100': '博物馆',
    '140200': '展览馆',
    '140300': '会展中心',
    '140400': '美术馆',
    '140500': '图书馆',
    '140600': '科技馆',
    '140700': '天文馆',
    '140800': '文化宫',
}

// 配置
const API_KEY = process.env.AMAP_API_KEY || '';
const API_SECRET = process.env.AMAP_SECRET || '';
const API_BASE_URL = 'https://restapi.amap.com/v5/place/text';
const QPS = 2; // 每秒2个请求
const REQUEST_INTERVAL = 1000 / QPS; // 500ms
const MAX_PAGES = 8; // 最多8页，每页25个，共200个
const PAGE_SIZE = 25;
const SHOW_FIELDS = 'children,business,indoor,navi,photos';

// 日志文件路径
const LOG_FILE = 'amap.log';
// 结果保存目录
const RESULTS_DIR = './json-results';

// 确保目录存在
if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
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
 * 生成签名
 */
function generateSig(params: Record<string, string | number | boolean>): string {
    // 按key排序
    const sortedKeys = Object.keys(params).sort();
    const queryString = sortedKeys
        .map(key => `${key}=${params[key]}`)
        .join('&');
    const stringToSign = `${queryString}&key=${API_KEY}`;
    const sig = createHash('md5').update(stringToSign + API_SECRET).digest('hex');
    return sig;
}

/**
 * 延迟函数
 */
function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 发送API请求
 */
async function fetchPOIData(
    keyword: string,
    types: string,
    region: string,
    pageNum: number
): Promise<Response> {
    const params: SearchParams = {
        keywords: keyword,
        types: types,
        region: region,
        city_limit: true,
        show_fields: SHOW_FIELDS,
        page_size: PAGE_SIZE,
        page_num: pageNum,
        output: 'json',
        key: API_KEY,
    };

    // 如果有secret，生成签名
    if (API_SECRET) {
        const sigParams: Record<string, string | number | boolean> = {
            keywords: params.keywords,
            types: params.types,
            region: params.region,
            city_limit: params.city_limit,
            show_fields: params.show_fields,
            page_size: params.page_size,
            page_num: params.page_num,
            output: params.output,
        };
        params.sig = generateSig(sigParams);
    }

    const queryString = Object.entries(params)
        .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
        .join('&');

    const url = `${API_BASE_URL}?${queryString}`;
    
    log(`请求: ${keyword} | ${types} | ${region} | 页码: ${pageNum}`);
    
    try {
        const response = await fetch(url);
        const data: Response = await response.json();
        
        if (data.status === '1' && data.infocode === '10000') {
            const count = parseInt(data.count || '0', 10);
            log(`成功: 返回 ${count} 条数据`);
            return data;
        } else {
            log(`错误: ${data.info || '未知错误'} (${data.infocode || 'N/A'})`);
            throw new Error(data.info || 'API请求失败');
        }
    } catch (error) {
        log(`异常: ${error instanceof Error ? error.message : String(error)}`);
        throw error;
    }
}

/**
 * 保存数据到文件
 */
function saveData(keyword: string, types: string, region: string, pageNum: number, data: Response) {
    const filename = `${keyword}_${types}_${region}_page${pageNum}.json`;
    const filepath = path.join(RESULTS_DIR, filename);
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf-8');
    log(`保存: ${filepath}`);
}

/**
 * 抓取单个关键词和类型的所有数据
 */
async function scrapeKeywordAndType(
    keyword: string,
    types: string,
    region: string
): Promise<void> {
    log(`开始抓取: 关键词=${keyword}, 类型=${types}, 区域=${region}`);
    
    let pageNum = 1;
    let hasMore = true;
    let totalCount = 0;

    // while (hasMore) {
    while (hasMore && pageNum <= MAX_PAGES) {
        // QPS控制：等待间隔
        if (pageNum > 1) {
            await delay(REQUEST_INTERVAL);
        }

        try {
            const response = await fetchPOIData(keyword, types, region, pageNum);
            
            if (response.pois && response.pois.length > 0) {
                saveData(keyword, types, region, pageNum, response);
                totalCount += response.pois.length;
                
                // 如果返回的数据少于page_size，说明没有更多数据了
                if (response.pois.length < PAGE_SIZE) {
                    hasMore = false;
                }
            } else {
                hasMore = false;
            }
            
            pageNum++;
        } catch (error) {
            log(`抓取失败，跳过: ${error instanceof Error ? error.message : String(error)}`);
            // 如果出错，继续下一页（可能是网络问题）
            pageNum++;
            // 如果连续失败，停止
            if (pageNum > MAX_PAGES) {
                hasMore = false;
            }
        }
    }

    log(`完成抓取: 关键词=${keyword}, 类型=${types}, 区域=${region}, 共 ${totalCount} 条数据`);
}

/**
 * 主函数：抓取所有数据
 */
async function main() {
    log('=== 开始数据抓取任务 ===');
    
    if (!API_KEY) {
        log('错误: 未设置 AMAP_API_KEY 环境变量');
        process.exit(1);
    }

    // 构建抓取任务列表
    const tasks: Array<{ keyword: string; types: string; region: string }> = [];

    
    // 2. 景点
    for (const region of adcodes) {
        for (const type of poiAttractions) {
            tasks.push({ keyword: '景点', types: type, region });
        }
    }


    // 3. 科教文化服务
    for (const region of adcodes) {
        for (const type of poiSciences) {
            const keyword = keywordMap[type] || type;
            tasks.push({ keyword, types: type, region });
        }
    }
    
    // 1. 酒店
    for (const region of adcodes) {
        for (const type of poiHotel) {
            tasks.push({ keyword: '酒店', types: type, region });
        }
    }

    log(`总共 ${tasks.length} 个抓取任务`);

    // 执行所有任务
    for (let i = 0; i < tasks.length; i++) {
        // 503 任务需要重试
        if(i + 1 != 503) continue;
        // if(i + 1 < 19) continue; // 跳过前19个任务
        const task = tasks[i];
        log(`进度: ${i + 1}/${tasks.length}`);
        await scrapeKeywordAndType(task.keyword, task.types, task.region);
        
        // 任务之间的延迟
        if (i < tasks.length - 1) {
            await delay(REQUEST_INTERVAL);
        }
    }

    log('=== 数据抓取任务完成 ===');
}

// 运行主函数
main().catch(error => {
    log(`致命错误: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
});
