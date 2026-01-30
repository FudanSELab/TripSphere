import * as fs from 'fs';

// POI type codes related to hotels
const hotelTypeCodes = [
    '100000', // Accommodation services major category
    '100100',
    '100101',
    '100102',
    '100103',
    '100104',
    '100105',
    '100200',
    '100201',
];

interface POI {
    typecode?: string | boolean;
    [key: string]: any;
}

function isHotelPOI(poi: POI): boolean {
    // Check if typecode starts with '100' (Accommodation services major category)
    return typeof poi.typecode === 'string' && poi.typecode.startsWith('100');
}

function main() {
    console.log('Starting statistics on POI data in JSON file...\n');
    
    // Read JSON file
    const filePath = './json-results-merge.json';
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const pois: POI[] = JSON.parse(fileContent);
    
    // Total count
    const totalCount = pois.length;
    
    // Hotel POI count
    const hotelPOIs = pois.filter(isHotelPOI);
    const hotelCount = hotelPOIs.length;
    
    // Hotel POI count by type code
    const hotelByType: Record<string, number> = {};
    hotelPOIs.forEach(poi => {
        const typeCode = typeof poi.typecode === 'string' ? poi.typecode : 'unknown';
        hotelByType[typeCode] = (hotelByType[typeCode] || 0) + 1;
    });
    
    // Output statistical results
    console.log('='.repeat(50));
    console.log('Statistical Results');
    console.log('='.repeat(50));
    console.log(`Total POI Count: ${totalCount.toLocaleString()}`);
    console.log(`Hotel POI Count: ${hotelCount.toLocaleString()}`);
    console.log(`Hotel POI Ratio: ${((hotelCount / totalCount) * 100).toFixed(2)}%`);
    console.log('\nHotel POI Distribution by Type Code:');
    console.log('-'.repeat(50));
    
    // Sort by count and output
    const sortedTypes = Object.entries(hotelByType)
        .sort((a, b) => b[1] - a[1]);
    
    sortedTypes.forEach(([typeCode, count]) => {
        console.log(`  ${typeCode}: ${count.toLocaleString()}`);
    });
    
    console.log('='.repeat(50));
}

main();
