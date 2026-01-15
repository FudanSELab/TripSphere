/**
 * 高德地图API响应类型定义
 */
export interface Response {
    /**
     * 单次请求返回的实际poi点的个数
     */
    count?: string;
    /**
     *
     * 访问状态值的说明，如果成功返回"ok"，失败返回错误原因，具体见[错误码说明](https://lbs.amap.com/api/webservice/guide/tools/info)。
     */
    info?: string;
    /**
     * 返回状态说明,10000代表正确,详情参阅info状态表
     */
    infocode?: string;
    /**
     * 返回的poi完整集合
     */
    pois?: Pois[];
    /**
     * 本次API访问状态，如果成功返回1，如果失败返回0。
     */
    status?: string;
    [property: string]: any;
}

/**
 * 返回的poi完整集合
 */
export interface Pois {
    /**
     * poi所属区域编码
     */
    adcode?: string;
    /**
     * poi详细地址
     */
    address?: string;
    /**
     * poi所属区县
     */
    adname?: string;
    /**
     * 设置后返回子POI信息
     */
    children?: Children[];
    /**
     * poi所属城市编码
     */
    citycode?: string;
    /**
     * poi所属城市
     */
    cityname?: string;
    /**
     * poi唯一标识
     */
    id?: string;
    /**
     * poi经纬度
     */
    location?: string;
    /**
     * poi名称
     */
    name?: string;
    /**
     * poi所属省份编码
     */
    pcode?: string;
    /**
     * poi所属省份
     */
    pname?: string;
    /**
     * 单个poi内包含的完整返回数据
     */
    poi?: string;
    /**
     * poi所属类型
     */
    type?: string;
    /**
     * poi分类编码
     */
    typecode?: string;
    [property: string]: any;
}

/**
 * 设置后返回子POI信息
 */
export interface Children {
    /**
     * 子poi详细地址
     */
    address?: string;
    /**
     * 设置后返回poi商业信息
     */
    business?: Business;
    /**
     * 子poi唯一标识
     */
    id?: string;
    /**
     * 子poi经纬度
     */
    location?: string;
    /**
     * 子poi名称
     */
    name?: string;
    /**
     * 子poi所属类型
     */
    subtype?: string;
    /**
     * 子poi分类编码
     */
    typecode?: string;
    [property: string]: any;
}

/**
 * 设置后返回poi商业信息
 */
export interface Business {
    /**
     * poi的别名，无别名时不返回
     */
    alias?: string;
    /**
     * poi所属商圈
     */
    business_area?: string;
    /**
     * poi人均消费，目前仅在餐饮、酒店、景点、影院类POI下返回
     */
    cost?: string;
    /**
     * 设置后返回室内相关信息
     */
    indoor?: Indoor;
    /**
     * poi今日营业时间，如 08:30-17:30 08:30-09:00 12:00-13:30 09:00-13:00
     */
    opentime_today?: string;
    /**
     * poi营业时间描述，如
     * 周一至周五:08:30-17:30(延时服务时间:08:30-09:00；12:00-13:30)；周六延时服务时间:09:00-13:00(法定节假日除外)
     */
    opentime_week?: string;
    /**
     * 停车场类型（地下、地面、路边），目前仅在停车场类POI下返回
     */
    parking_type?: string;
    /**
     * poi评分，目前仅在餐饮、酒店、景点、影院类POI下返回
     */
    rating?: string;
    /**
     * poi特色内容，目前仅在美食poi下返回
     */
    tag?: string;
    /**
     * poi的联系电话
     */
    tel?: string;
    [property: string]: any;
}

/**
 * 设置后返回室内相关信息
 */
export interface Indoor {
    /**
     * 是否有室内地图标志，1为有，0为没有
     */
    indoor_map?: string;
    /**
     * 如果当前POI为建筑物类POI，则cpid为自身POI ID；如果当前POI为商铺类POI，则cpid为其所在建筑物的POI ID。  indoor_map为0时不返回
     */
    cpid?: string;
    /**
     * 楼层索引，一般会用数字表示，例如8；indoor_map为0时不返回
     */
    floor?: string;
    /**
     * 设置后返回导航位置相关信息
     */
    navi?: Navi;
    /**
     * 所在楼层，一般会带有字母，例如F8；indoor_map为0时不返回
     */
    truefloor?: string;
    [property: string]: any;
}

/**
 * 设置后返回导航位置相关信息
 */
export interface Navi {
    /**
     * poi的入口经纬度坐标
     */
    entr_location?: string;
    /**
     * poi的出口经纬度坐标
     */
    exit_location?: string;
    /**
     * poi的地理格id
     */
    gridcode?: string;
    /**
     * poi对应的导航引导点坐标。大型面状POI的导航引导点，一般为各类出入口，方便结合导航、路线规划等服务使用
     */
    navi_poiid?: string;
    /**
     * 设置后返回poi图片相关信息
     */
    photos?: Photos[];
    [property: string]: any;
}

/**
 * 设置后返回poi图片相关信息
 */
export interface Photos {
    /**
     * poi的图片介绍
     */
    title?: string;
    /**
     * poi图片的下载链接
     */
    url?: string;
    [property: string]: any;
}

/**
 * API请求参数
 */
export interface SearchParams {
    keywords: string;
    types: string; // POI 分类码
    region: string; // adcode 区域码
    city_limit: boolean;
    show_fields: string; // 确定需要的字段
    page_size: number; // 1-25
    page_num: number; // 1-100
    sig?: string; // 数字签名
    output: string;
    callback?: string;
    key: string; // API Key
}
