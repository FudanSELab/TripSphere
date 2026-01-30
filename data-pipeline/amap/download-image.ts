import * as fs from 'fs';
import * as path from 'path';
import lodash from 'lodash';

// Configuration
const QPS = 2; // 2 requests per second
const REQUEST_INTERVAL = 1000 / QPS; // 500ms
const BATCH_SIZE = 20; // Number of POIs to process in parallel each time

// Log file path
const LOG_FILE = 'amap.log';
// JSON results file
const MERGED_JSON_FILE = './json-results-merge.json';
// Image save directory
const IMAGE_DIR = './image-results';

// Ensure directory exists
if (!fs.existsSync(IMAGE_DIR)) {
    fs.mkdirSync(IMAGE_DIR, { recursive: true });
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
 * Delay function
 */
function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Download image
 */
async function downloadImage(url: string, savePath: string): Promise<void> {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const arrayBuffer = await response.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        
        // Get file extension from Content-Type, default to jpg if none
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
        log(`Download image: ${filepath}`);
    } catch (error) {
        log(`Failed to download image ${url}: ${error instanceof Error ? error.message : String(error)}`);
        throw error;
    }
}

/**
 * Download all photos of a POI (parallel download)
 */
async function downloadPOIPhotos(poi: { id?: string; photos?: Array<{ title?: string; url?: string }> }): Promise<void> {
    if (!poi.id || !poi.photos || poi.photos.length === 0) {
        return;
    }
    
    const poiId = poi.id;
    const dirPath = path.join(IMAGE_DIR, poiId);
    
    // Ensure directory exists
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
    
    // Build all download tasks
    const downloadTasks = poi.photos
        .map((photo, index) => {
            if (!photo.url) {
                return null;
            }
            const savePath = path.join(dirPath, `${index}`);
            return downloadImage(photo.url, savePath).catch(error => {
                // Log download failure but continue processing other images
                log(`Skip photo download: ${poiId}/${index}`);
            });
        })
        .filter((task): task is Promise<void> => task !== null);
    
    // Execute all download tasks in parallel
    await Promise.all(downloadTasks);
}

/**
 * Process POI array in batches, processing a specified number of POIs in parallel each time
 */
async function processPOIsInBatches(pois: Array<{ id?: string; photos?: Array<{ title?: string; url?: string }> }>): Promise<void> {
    const total = pois.length;
    log(`Start processing ${total} POIs, ${BATCH_SIZE} per batch`);

    const chunks = lodash.chunk(pois, BATCH_SIZE);
    const totalBatches = chunks.length;
    
    for (let i = 0; i < chunks.length; i++) {
        // Start from the 55th batch, previously 5 per batch, reached 237
        if(i < 55) continue;
        
        const batch = chunks[i];
        const batchNumber = i + 1;
        const startIndex = i * BATCH_SIZE + 1;
        const endIndex = Math.min((i + 1) * BATCH_SIZE, total);
        
        log(`Processing batch ${batchNumber}/${totalBatches} (POI ${startIndex}-${endIndex})`);
        
        // Process all POIs in the current batch in parallel
        await Promise.all(batch.map(poi => downloadPOIPhotos(poi)));
        
        // Delay between batches to avoid excessive requests
        if (i < chunks.length - 1) {
            await delay(REQUEST_INTERVAL);
        }
    }
    
    log(`Finish processing all ${total} POIs`);
}

/**
 * Main function: Download all images
 */
async function main() {
    log('=== Start image download task ===');
    
    // Check if file exists
    if (!fs.existsSync(MERGED_JSON_FILE)) {
        log(`Error: File ${MERGED_JSON_FILE} does not exist`);
        process.exit(1);
    }
    
    try {
        // Read merged JSON file
        log(`Read file: ${MERGED_JSON_FILE}`);
        const fileContent = fs.readFileSync(MERGED_JSON_FILE, 'utf-8');
        const pois: Array<{ id?: string; photos?: Array<{ title?: string; url?: string }> }> = JSON.parse(fileContent);
        
        if (!Array.isArray(pois)) {
            log(`Error: File ${MERGED_JSON_FILE} is not an array`);
            process.exit(1);
        }
        
        if (pois.length === 0) {
            log(`Warning: No POI data in file ${MERGED_JSON_FILE}`);
            process.exit(0);
        }
        
        log(`File contains ${pois.length} POIs`);
        
        // Process POIs in batches
        await processPOIsInBatches(pois);
        
        log('=== Image download task complete ===');
    } catch (error) {
        log(`Failed to process file ${MERGED_JSON_FILE}: ${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    }
}

// Run main function
main().catch(error => {
    log(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
});
