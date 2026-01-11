import * as fs from 'fs';

// 酒店相关的 POI 类型码
const hotelTypeCodes = [
    '100000', // 住宿服务大类
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
    // 检查 typecode 是否以 '100' 开头（住宿服务大类）
    return typeof poi.typecode === 'string' && poi.typecode.startsWith('100');
}

function main() {
    console.log('开始统计 JSON 文件中的 POI 数据...\n');
    
    // 读取 JSON 文件
    const filePath = './json-results-merge.json';
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const pois: POI[] = JSON.parse(fileContent);
    
    // 统计总数
    const totalCount = pois.length;
    
    // 统计酒店 POI
    const hotelPOIs = pois.filter(isHotelPOI);
    const hotelCount = hotelPOIs.length;
    
    // 按类型码统计酒店 POI
    const hotelByType: Record<string, number> = {};
    hotelPOIs.forEach(poi => {
        const typeCode = typeof poi.typecode === 'string' ? poi.typecode : 'unknown';
        hotelByType[typeCode] = (hotelByType[typeCode] || 0) + 1;
    });
    
    // 输出统计结果
    console.log('='.repeat(50));
    console.log('统计结果');
    console.log('='.repeat(50));
    console.log(`总 POI 数量: ${totalCount.toLocaleString()}`);
    console.log(`酒店 POI 数量: ${hotelCount.toLocaleString()}`);
    console.log(`酒店 POI 占比: ${((hotelCount / totalCount) * 100).toFixed(2)}%`);
    console.log('\n酒店 POI 按类型码分布:');
    console.log('-'.repeat(50));
    
    // 按数量排序输出
    const sortedTypes = Object.entries(hotelByType)
        .sort((a, b) => b[1] - a[1]);
    
    sortedTypes.forEach(([typeCode, count]) => {
        console.log(`  ${typeCode}: ${count.toLocaleString()}`);
    });
    
    console.log('='.repeat(50));
}

main();
