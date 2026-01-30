/**
 * Amap Map API response type definitions
 */
export interface Response {
    /**
     * Number of POIs returned in a single request
     */
    count?: string;
    /**
     * Description of the access status value. 
     * If successful, returns "ok"; if failed, returns the reason for failure. 
     * See [Error Code Description](https://lbs.amap.com/api/webservice/guide/tools/info) for details.
     */
    info?: string;
    /**
     * Return status description, 10000 represents success, see info status table for details
     */
    infocode?: string;
    /**
     * Full collection of returned POIs
     */
    pois?: Pois[];
    /**
     * Access status of this API call, 1 for success, 0 for failure.
     */
    status?: string;
    [property: string]: any;
}

/**
 * Full collection of returned POIs
 */
export interface Pois {
    /**
     * Region code of the POI
     */
    adcode?: string;
    /**
     * Detailed address of the POI
     */
    address?: string;
    /**
     * District/County name of the POI
     */
    adname?: string;
    /**
     * If set, returns sub-POI information
     */
    children?: Children[];
    /**
     * City code of the POI
     */
    citycode?: string;
    /**
     * City name of the POI
     */
    cityname?: string;
    /**
     * Unique identifier of the POI
     */
    id?: string;
    /**
     * Longitude and latitude of the POI
     */
    location?: string;
    /**
     * Name of the POI
     */
    name?: string;
    /**
     * Province code of the POI
     */
    pcode?: string;
    /**
     * Province name of the POI
     */
    pname?: string;
    /**
     * Complete return data contained within a single POI
     */
    poi?: string;
    /**
     * Type of the POI
     */
    type?: string;
    /**
     * Type code of the POI
     */
    typecode?: string;
    [property: string]: any;
}

/**
 * If set, returns sub-POI information
 */
export interface Children {
    /**
     * Detailed address of the sub-POI
     */
    address?: string;
    /**
     * If set, returns business information of the POI
     */
    business?: Business;
    /**
     * Unique identifier of the sub-POI
     */
    id?: string;
    /**
     * Longitude and latitude of the sub-POI
     */
    location?: string;
    /**
     * Name of the sub-POI
     */
    name?: string;
    /**
     * Sub-type of the sub-POI
     */
    subtype?: string;
    /**
     * Category code of the sub-POI
     */
    typecode?: string;
    [property: string]: any;
}

/**
 * If set, returns business information of the POI
 */
export interface Business {
    /**
     * Alias of the POI, not returned if there is no alias
     */
    alias?: string;
    /**
     * Business area of the POI
     */
    business_area?: string;
    /**
     * Per capita consumption, currently only returned for food, hotel, attraction, and cinema POIs
     */
    cost?: string;
    /**
     * If set, returns indoor-related information
     */
    indoor?: Indoor;
    /**
     * Today's business hours, e.g., 08:30-17:30 08:30-09:00 12:00-13:30 09:00-13:00
     */
    opentime_today?: string;
    /**
     * Business hours description, e.g., 
     * Monday to Friday: 08:30-17:30 (Delay service: 08:30-09:00; 12:00-13:30); Saturday delay service: 09:00-13:00 (except statutory holidays)
     */
    opentime_week?: string;
    /**
     * Parking type (underground, ground, roadside), currently only returned for parking lot POIs
     */
    parking_type?: string;
    /**
     * POI rating, currently only returned for food, hotel, attraction, and cinema POIs
     */
    rating?: string;
    /**
     * Featured content, currently only returned for gourmet POIs
     */
    tag?: string;
    /**
     * Contact phone number of the POI
     */
    tel?: string;
    [property: string]: any;
}

/**
 * If set, returns indoor-related information
 */
export interface Indoor {
    /**
     * Indoor map flag, 1 for yes, 0 for no
     */
    indoor_map?: string;
    /**
     * If the current POI is a building POI, cpid is its own POI ID; if it's a shop POI, cpid is the POI ID of the building it's in. Not returned if indoor_map is 0.
     */
    cpid?: string;
    /**
     * Floor index, usually represented by a number, e.g., 8; not returned if indoor_map is 0.
     */
    floor?: string;
    /**
     * If set, returns navigation location information
     */
    navi?: Navi;
    /**
     * Floor location, usually with a letter, e.g., F8; not returned if indoor_map is 0.
     */
    truefloor?: string;
    [property: string]: any;
}

/**
 * If set, returns navigation location information
 */
export interface Navi {
    /**
     * Latitude and longitude of the POI entrance
     */
    entr_location?: string;
    /**
     * Latitude and longitude of the POI exit
     */
    exit_location?: string;
    /**
     * Grid code ID of the POI
     */
    gridcode?: string;
    /**
     * Navigation guidance coordinates. For large area POIs, these are usually various entrances/exits, convenient for use with navigation and route planning.
     */
    navi_poiid?: string;
    /**
     * If set, returns POI photo information
     */
    photos?: Photos[];
    [property: string]: any;
}

/**
 * If set, returns POI photo information
 */
export interface Photos {
    /**
     * Photo title/description of the POI
     */
    title?: string;
    /**
     * Download URL for the POI photo
     */
    url?: string;
    [property: string]: any;
}

/**
 * API request parameters
 */
export interface SearchParams {
    keywords: string;
    types: string; // POI Category Code
    region: string; // adcode Region Code
    city_limit: boolean;
    show_fields: string; // Fields to return
    page_size: number; // 1-25
    page_num: number; // 1-100
    sig?: string; // Digital signature
    output: string;
    callback?: string;
    key: string; // API Key
}
