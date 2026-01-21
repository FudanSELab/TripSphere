import logging

import grpc
from langchain_core.tools import tool  # type: ignore
from pydantic import BaseModel, Field
from tripsphere.attraction import attraction_pb2, attraction_pb2_grpc
from tripsphere.common import geo_pb2

logger = logging.getLogger(__name__)


class AttractionDetail(BaseModel):
    """Detailed information about an attraction."""

    id: str = Field(description="Attraction ID")
    name: str = Field(description="Attraction name")
    description: str = Field(description="Detailed description")
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    address: str = Field(description="Full address")
    tags: list[str] = Field(default_factory=list, description="Tags/categories")
    estimated_visit_duration_hours: float = Field(
        default=2.0, description="Typical visit duration in hours"
    )
    estimated_cost: float = Field(default=0.0, description="Estimated entrance fee")
    opening_hours: str = Field(default="09:00-18:00", description="Opening hours")


class AttractionSearchResult(BaseModel):
    """Search result with list of attractions."""

    attractions: list[AttractionDetail] = Field(description="List of attractions found")


@tool
async def search_attractions_nearby(
    center_longitude: float,
    center_latitude: float,
    radius_km: float = 20.0,
    tags: list[str] | None = None,
    limit: int = 50,
) -> AttractionSearchResult:
    """Search for attractions near a location using gRPC AttractionService.

    Arguments:
        center_latitude: Center point latitude
        center_longitude: Center point longitude
        radius_km: Search radius in kilometers (default: 20km)
        tags: Filter by tags (e.g., ["cultural", "museum", "food"])
        limit: Maximum number of results (default: 50)

    Returns:
        AttractionSearchResult with matching attractions sorted by distance
    """
    logger.info(
        f"Searching attractions near ({center_longitude}, {center_latitude}) "
        f"within {radius_km}km, tags: {tags}, limit: {limit}"
    )

    location = geo_pb2.Location(latitude=center_latitude, longitude=center_longitude)
    request = attraction_pb2.FindAttractionsWithinRadiusRequest(
        location=location, radius_km=radius_km
    )
    async with grpc.aio.insecure_channel("localhost:50053") as channel:
        stub = attraction_pb2_grpc.AttractionServiceStub(channel)
        response = await stub.FindAttractionsWithinRadius(request)

    attractions = response.content
    attraction_details: list[AttractionDetail] = []
    for attraction in attractions:
        attraction_detail = AttractionDetail(
            id=attraction.id,
            name=attraction.name,
            description=attraction.introduction,
            latitude=attraction.location.longitude,
            longitude=attraction.location.latitude,
            address=(
                f"{attraction.address.province} {attraction.address.city} "
                f"{attraction.address.county} {attraction.address.district} "
                f"{attraction.address.street}"
            ),
            tags=list[str](attraction.tags),
        )
        attraction_details.append(attraction_detail)

    return AttractionSearchResult(attractions=attraction_details)

    # MOCK DATA - Replace with actual gRPC call
    # Generate realistic mock attractions for Shanghai
    mock_shanghai_attractions = [
        AttractionDetail(
            id="attr_001",
            name="外滩",
            description="上海最具标志性的滨江区域，拥有历史建筑群和现代天际线美景",
            latitude=31.2400,
            longitude=121.4900,
            address="上海市黄浦区中山东一路",
            tags=["地标", "观光", "历史", "摄影"],
            estimated_visit_duration_hours=2.0,
            estimated_cost=0.0,
            opening_hours="00:00-23:59",
        ),
        AttractionDetail(
            id="attr_002",
            name="豫园",
            description="明代私家园林，展现江南园林建筑艺术精华",
            latitude=31.2267,
            longitude=121.4921,
            address="上海市黄浦区豫园老街279号",
            tags=["文化", "历史", "园林", "古迹"],
            estimated_visit_duration_hours=2.5,
            estimated_cost=40.0,
            opening_hours="08:45-17:00",
        ),
        AttractionDetail(
            id="attr_003",
            name="南京路步行街",
            description="中国最繁华的商业街之一，汇集众多品牌店铺和美食",
            latitude=31.2352,
            longitude=121.4779,
            address="上海市黄浦区南京东路",
            tags=["购物", "美食", "地标"],
            estimated_visit_duration_hours=3.0,
            estimated_cost=0.0,
            opening_hours="00:00-23:59",
        ),
        AttractionDetail(
            id="attr_004",
            name="上海博物馆",
            description="中国古代艺术博物馆，收藏大量珍贵文物",
            latitude=31.2280,
            longitude=121.4750,
            address="上海市黄浦区人民大道201号",
            tags=["文化", "博物馆", "历史", "教育"],
            estimated_visit_duration_hours=3.0,
            estimated_cost=0.0,
            opening_hours="09:00-17:00",
        ),
        AttractionDetail(
            id="attr_005",
            name="东方明珠",
            description="上海标志性电视塔，可俯瞰整个城市美景",
            latitude=31.2397,
            longitude=121.4992,
            address="上海市浦东新区世纪大道1号",
            tags=["地标", "观光", "摄影"],
            estimated_visit_duration_hours=2.0,
            estimated_cost=180.0,
            opening_hours="08:00-22:00",
        ),
        AttractionDetail(
            id="attr_006",
            name="城隍庙",
            description="上海著名道观，周边小吃街汇集众多传统美食",
            latitude=31.2256,
            longitude=121.4920,
            address="上海市黄浦区方浜中路249号",
            tags=["文化", "宗教", "美食", "历史"],
            estimated_visit_duration_hours=1.5,
            estimated_cost=10.0,
            opening_hours="08:30-16:30",
        ),
        AttractionDetail(
            id="attr_007",
            name="田子坊",
            description="艺术创意街区，保留石库门建筑风格",
            latitude=31.2103,
            longitude=121.4690,
            address="上海市黄浦区泰康路210弄",
            tags=["艺术", "文化", "购物", "摄影"],
            estimated_visit_duration_hours=2.0,
            estimated_cost=0.0,
            opening_hours="10:00-22:00",
        ),
        AttractionDetail(
            id="attr_008",
            name="新天地",
            description="时尚休闲街区，融合历史建筑与现代商业",
            latitude=31.2196,
            longitude=121.4745,
            address="上海市黄浦区太仓路181弄",
            tags=["购物", "美食", "夜生活", "历史"],
            estimated_visit_duration_hours=2.5,
            estimated_cost=0.0,
            opening_hours="10:00-23:00",
        ),
        AttractionDetail(
            id="attr_009",
            name="上海迪士尼乐园",
            description="中国大陆首座迪士尼主题乐园",
            latitude=31.1434,
            longitude=121.6608,
            address="上海市浦东新区川沙镇黄赵路310号",
            tags=["娱乐", "主题公园", "亲子"],
            estimated_visit_duration_hours=8.0,
            estimated_cost=399.0,
            opening_hours="08:30-22:00",
        ),
        AttractionDetail(
            id="attr_010",
            name="朱家角古镇",
            description="江南水乡古镇，保存完好的明清建筑",
            latitude=31.1095,
            longitude=121.0549,
            address="上海市青浦区朱家角镇",
            tags=["古镇", "历史", "文化", "摄影"],
            estimated_visit_duration_hours=4.0,
            estimated_cost=30.0,
            opening_hours="08:30-17:00",
        ),
        AttractionDetail(
            id="attr_011",
            name="静安寺",
            description="上海最古老的寺庙之一，位于繁华商圈中心",
            latitude=31.2244,
            longitude=121.4452,
            address="上海市静安区南京西路1686号",
            tags=["宗教", "文化", "历史"],
            estimated_visit_duration_hours=1.0,
            estimated_cost=50.0,
            opening_hours="07:30-17:00",
        ),
        AttractionDetail(
            id="attr_012",
            name="鲁迅公园",
            description="纪念文学家鲁迅的公园，环境优美",
            latitude=31.2661,
            longitude=121.4865,
            address="上海市虹口区四川北路2288号",
            tags=["公园", "文化", "休闲"],
            estimated_visit_duration_hours=1.5,
            estimated_cost=0.0,
            opening_hours="06:00-18:00",
        ),
    ]

    # Filter by tags if provided
    if tags and len(tags) > 0:
        filtered_attractions = [
            attr
            for attr in mock_shanghai_attractions
            if any(tag in attr.tags for tag in tags)
        ]
    else:
        filtered_attractions = mock_shanghai_attractions

    # Limit results
    limited_attractions = filtered_attractions[:limit]

    logger.info(f"Found {len(limited_attractions)} attractions (MOCK DATA)")

    return AttractionSearchResult(attractions=limited_attractions)


@tool
async def get_attraction_details(attraction_id: str) -> AttractionDetail:
    """Get detailed information about a specific attraction.

    Arguments:
        attraction_id: The attraction ID to fetch details for

    Returns:
        AttractionDetail with complete attraction information
    """
    logger.info(f"Fetching details for attraction: {attraction_id}")

    # TODO: Implement actual gRPC call to AttractionService
    # Service: AttractionService.FindAttractionById
    # Request: FindAttractionByIdRequest { id: string }
    # Response: FindAttractionByIdResponse { attraction: Attraction }

    # MOCK DATA - Return mock attraction based on ID
    mock_attractions_map = {
        "attr_001": AttractionDetail(
            id="attr_001",
            name="外滩",
            description="上海最具标志性的滨江区域，拥有历史建筑群和现代天际线美景。沿江1.5公里的万国建筑博览群展现了哥特式、罗马式、巴洛克等多种建筑风格。",
            latitude=31.2400,
            longitude=121.4900,
            address="上海市黄浦区中山东一路",
            tags=["地标", "观光", "历史", "摄影"],
            estimated_visit_duration_hours=2.0,
            estimated_cost=0.0,
            opening_hours="00:00-23:59",
        ),
        "attr_002": AttractionDetail(
            id="attr_002",
            name="豫园",
            description="始建于明嘉靖年间的私家园林，是江南古典园林的代表作。园内有三穗堂、大假山、点春堂等40余处景点，充分展现了明清江南园林建筑艺术。",
            latitude=31.2267,
            longitude=121.4921,
            address="上海市黄浦区豫园老街279号",
            tags=["文化", "历史", "园林", "古迹"],
            estimated_visit_duration_hours=2.5,
            estimated_cost=40.0,
            opening_hours="08:45-17:00",
        ),
    }

    if attraction_id in mock_attractions_map:
        result = mock_attractions_map[attraction_id]
        logger.info(f"Found attraction details (MOCK): {result.name}")
        return result

    # Default fallback
    logger.warning(
        f"Attraction {attraction_id} not found in mock data, returning placeholder"
    )
    return AttractionDetail(
        id=attraction_id,
        name=f"Attraction {attraction_id}",
        description="Mock attraction description",
        latitude=31.2304,
        longitude=121.4737,
        address="Shanghai, China",
        tags=["sightseeing"],
        estimated_visit_duration_hours=2.0,
        estimated_cost=0.0,
    )
