import * as fs from 'fs';
import * as path from 'path';
import { createHash } from 'crypto';
import { Response, SearchParams } from './types';

// adcode for each region
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

// POI category code mapping
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

// Keyword mapping
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

// Configuration
const API_KEY = process.env.AMAP_API_KEY || '';
const API_SECRET = process.env.AMAP_SECRET || '';
const API_BASE_URL = 'https://restapi.amap.com/v5/place/text';
const QPS = 2; // 2 requests per second
const REQUEST_INTERVAL = 1000 / QPS; // 500ms
const MAX_PAGES = 8; // Max 8 pages, 25 items per page, total 200
const PAGE_SIZE = 25;
const SHOW_FIELDS = 'children,business,indoor,navi,photos';

// Log file path
const LOG_FILE = 'amap.log';
// Results directory
const RESULTS_DIR = './json-results';

// Ensure directory exists
if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
}

/**
 * Write log
 */
function log(message: string) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    fs.appendFileSync(LOG_FILE, logMessage);
    console.log(logMessage.trim());
}

/**
 * Generate signature
 */
function generateSig(params: Record<string, string | number | boolean>): string {
    // Sort by key
    const sortedKeys = Object.keys(params).sort();
    const queryString = sortedKeys
        .map(key => `${key}=${params[key]}`)
        .join('&');
    const stringToSign = `${queryString}&key=${API_KEY}`;
    const sig = createHash('md5').update(stringToSign + API_SECRET).digest('hex');
    return sig;
}

/**
 * Delay function
 */
function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Send API request
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

    // Generate signature if secret is present
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
    
    log(`Request: ${keyword} | ${types} | ${region} | Page: ${pageNum}`);
    
    try {
        const response = await fetch(url);
        const data: Response = await response.json();
        
        if (data.status === '1' && data.infocode === '10000') {
            const count = parseInt(data.count || '0', 10);
            log(`Success: returned ${count} items`);
            return data;
        } else {
            log(`Error: ${data.info || 'Unknown error'} (${data.infocode || 'N/A'})`);
            throw new Error(data.info || 'API request failed');
        }
    } catch (error) {
        log(`Exception: ${error instanceof Error ? error.message : String(error)}`);
        throw error;
    }
}

/**
 * Save data to file
 */
function saveData(keyword: string, types: string, region: string, pageNum: number, data: Response) {
    const filename = `${keyword}_${types}_${region}_page${pageNum}.json`;
    const filepath = path.join(RESULTS_DIR, filename);
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf-8');
    log(`Saved: ${filepath}`);
}

/**
 * Scrape all data for a single keyword and type
 */
async function scrapeKeywordAndType(
    keyword: string,
    types: string,
    region: string
): Promise<void> {
    log(`Start scraping: keyword=${keyword}, types=${types}, region=${region}`);
    
    let pageNum = 1;
    let hasMore = true;
    let totalCount = 0;

    // while (hasMore) {
    while (hasMore && pageNum <= MAX_PAGES) {
        // QPS Control: Wait interval
        if (pageNum > 1) {
            await delay(REQUEST_INTERVAL);
        }

        try {
            const response = await fetchPOIData(keyword, types, region, pageNum);
            
            if (response.pois && response.pois.length > 0) {
                saveData(keyword, types, region, pageNum, response);
                totalCount += response.pois.length;
                
                // If returned data is less than page_size, no more data
                if (response.pois.length < PAGE_SIZE) {
                    hasMore = false;
                }
            } else {
                hasMore = false;
            }
            
            pageNum++;
        } catch (error) {
            log(`Scrape failed, skipping: ${error instanceof Error ? error.message : String(error)}`);
            // If error, continue to next page (could be network issue)
            pageNum++;
            // If continuous failure, stop
            if (pageNum > MAX_PAGES) {
                hasMore = false;
            }
        }
    }

    log(`Finish scraping: keyword=${keyword}, types=${types}, region=${region}, total ${totalCount} items`);
}

/**
 * Main function: Scrape all data
 */
async function main() {
    log('=== Start data scraping task ===');
    
    if (!API_KEY) {
        log('Error: AMAP_API_KEY environment variable not set');
        process.exit(1);
    }

    // Build scraping task list
    const tasks: Array<{ keyword: string; types: string; region: string }> = [];

    
    // 2. Attraction
    for (const region of adcodes) {
        for (const type of poiAttractions) {
            tasks.push({ keyword: '景点', types: type, region });
        }
    }


    // 3. Cultural and Educational Services
    for (const region of adcodes) {
        for (const type of poiSciences) {
            const keyword = keywordMap[type] || type;
            tasks.push({ keyword, types: type, region });
        }
    }
    
    // 1. Hotel
    for (const region of adcodes) {
        for (const type of poiHotel) {
            tasks.push({ keyword: '酒店', types: type, region });
        }
    }

    log(`Total ${tasks.length} scraping tasks`);

    // Execute all tasks
    for (let i = 0; i < tasks.length; i++) {
        // Task 503 needs retry
        if(i + 1 != 503) continue;
        // if(i + 1 < 19) continue; // Skip first 19 tasks
        const task = tasks[i];
        log(`Progress: ${i + 1}/${tasks.length}`);
        await scrapeKeywordAndType(task.keyword, task.types, task.region);
        
        // Delay between tasks
        if (i < tasks.length - 1) {
            await delay(REQUEST_INTERVAL);
        }
    }

    log('=== Data scraping task complete ===');
}

// Run main function
main().catch(error => {
    log(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
});
