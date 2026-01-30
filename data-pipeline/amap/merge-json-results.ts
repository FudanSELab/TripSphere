import * as fs from 'fs';
import * as path from 'path';
import { Response } from './types';

// JSON results directory
const RESULTS_DIR = './json-results';
// Output file
const OUTPUT_FILE = './json-results-merge.json';

/**
 * Main function: Merge all JSON files
 */
function main() {
    console.log('=== Start merging JSON files ===\n');
    
    // Check if directory exists
    if (!fs.existsSync(RESULTS_DIR)) {
        console.error(`Error: Directory ${RESULTS_DIR} does not exist`);
        process.exit(1);
    }
    
    // Read all JSON files
    const files = fs.readdirSync(RESULTS_DIR)
        .filter(file => file.endsWith('.json'))
        .map(file => path.join(RESULTS_DIR, file))
        .sort(); // Sort to ensure consistent order
    
    if (files.length === 0) {
        console.log(`Warning: No JSON files found in ${RESULTS_DIR} directory`);
        process.exit(0);
    }
    
    console.log(`Found ${files.length} JSON files\n`);
    
    // Merge all POI data: Extract pois array from each JSON file and flatten into a large POI array
    // Use Map to de-duplicate based on poi.id
    const poiMap = new Map<string, any>();
    let processedFiles = 0;
    let errorFiles = 0;
    let totalPois = 0;
    let duplicateCount = 0;
    
    for (const file of files) {
        try {
            const fileContent = fs.readFileSync(file, 'utf-8');
            const data: Response = JSON.parse(fileContent);
            
            // Process only successful requests
            if (data.status === '1' && data.infocode === '10000' && data.pois) {
                // Extract pois array and flatten into poiMap (each element is a POI object)
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
                console.warn(`Skip file ${path.basename(file)}: status=${data.status}, infocode=${data.infocode}`);
                errorFiles++;
            }
        } catch (error) {
            console.error(`Failed to parse file ${path.basename(file)}: ${error instanceof Error ? error.message : String(error)}`);
            errorFiles++;
        }
    }
    
    // Convert Map to array
    const allPois = Array.from(poiMap.values());
    
    console.log(`Processing complete:`);
    console.log(`  Successfully processed: ${processedFiles} files`);
    console.log(`  Skipped/Error: ${errorFiles} files`);
    console.log(`  Total POI Count: ${totalPois}`);
    console.log(`  De-duplicated POI Count: ${allPois.length}`);
    console.log(`  Duplicate POI Count: ${duplicateCount}\n`);
    
    // Write merged file
    try {
        const outputData = JSON.stringify(allPois, null, 2);
        fs.writeFileSync(OUTPUT_FILE, outputData, 'utf-8');
        console.log(`✓ Merged results saved to: ${OUTPUT_FILE}`);
        console.log(`  File size: ${(outputData.length / 1024 / 1024).toFixed(2)} MB`);
    } catch (error) {
        console.error(`Failed to write file: ${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    }
    
    console.log('\n=== Merging complete ===');
}

// Run main function
main();
