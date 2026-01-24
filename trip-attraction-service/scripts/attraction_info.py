# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas>=2.3.3",
#     "grpcio>=1.76.0",
#     "httpx>=0.27.0",
#     "protobuf>=4.21.0",
#     "pymongo>=4.6.0",
# ]
# ///

"""Import attractions data to MongoDB"""

import json
import logging
import mimetypes
from pathlib import Path
from typing import Any

import grpc
import httpx
from pymongo import MongoClient, InsertOne
from pymongo.collection import Collection
from bson import ObjectId

from file import file_pb2, file_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

FILE_SERVICE_GRPC_ADDRESS = "47.120.37.103:50051"
SERVICE_NAME_OF_FILE = "trip-attraction-service"
MONGO_URI = "mongodb://root:fudanse@47.120.37.103:27017"
MONGO_DATABASE = "attraction_db"
MONGO_COLLECTION = "attractions"
SCRIPT_DIR = Path(__file__).parent
JSON_FILE = SCRIPT_DIR / "filtered_attractions.json"
PICTURES_DIR = SCRIPT_DIR / "selected-pictures"


def get_content_type(file_path: Path) -> str:
    """Get MIME type from file path"""
    content_type, _ = mimetypes.guess_type(str(file_path))
    return content_type or "application/octet-stream"


def upload_image(
    grpc_client: file_pb2_grpc.FileServiceStub,
    http_client: httpx.Client,
    image_path: Path,
    attraction_id: str,
    image_index: int,
) -> dict[str, Any] | None:
    """
    Upload image to file-service

    Args:
        grpc_client: gRPC client
        http_client: HTTP client for file upload
        image_path: Image file path
        attraction_id: Attraction ID
        image_index: Image index

    Returns:
        File object dict on success, None on failure
    """
    try:
        # Check if file exists
        if not image_path.exists():
            logger.warning(f"Image file does not exist: {image_path}")
            return None

        # Get file extension
        ext = image_path.suffix.lower()
        file_name = f"{attraction_id}_{image_index}{ext}"

        # Build file path
        # According to API docs: path can be empty (will generate UUID), but here we provide a meaningful path
        file_path = f"attractions/{attraction_id}/{file_name}"

        # Create GetUploadSignedUrl request
        # According to API docs: service and path fields are required, others can be omitted or empty
        file_info = file_pb2.File(
            service=SERVICE_NAME_OF_FILE,
            path=file_path,
            # Following fields not provided or left empty
            name="",
            content_type="",
            url="",
            bucket="",
        )
        request = file_pb2.GetUploadSignedUrlRequest(file=file_info)

        # Call gRPC interface to get upload signed URL
        logger.info(f"Getting upload signed URL: {file_path}")
        response = grpc_client.GetUploadSignedUrl(request, timeout=30.0)

        upload_url = response.file.url
        uploaded_file = response.file

        if not upload_url:
            logger.error(f"Received empty upload URL: {file_path}")
            return None

        # Read file content
        with open(image_path, "rb") as f:
            file_content = f.read()

        # Get Content-Type
        content_type = get_content_type(image_path)

        # Upload file to signed URL
        logger.info(f"Uploading file: {image_path.name} -> {upload_url[:50]}...")
        upload_response = http_client.put(
            upload_url,
            content=file_content,
            headers={"Content-Type": content_type},
            timeout=30.0,
        )
        upload_response.raise_for_status()

        logger.info(f"✓ Image upload successful: {image_path.name}")

        # Return File object dict (according to Java model field names)
        return {
            "name": file_name,
            "contentType": uploaded_file.content_type or content_type,
            "url": uploaded_file.url or upload_url,
            "bucket": uploaded_file.bucket,
            "service": uploaded_file.service,
            "path": uploaded_file.path,
        }
    except grpc.RpcError as e:
        logger.error(f"gRPC call failed {image_path}: {e.code()} - {e.details()}")
        return None
    except httpx.HTTPError as e:
        logger.error(f"HTTP upload failed {image_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Image upload failed {image_path}: {e}", exc_info=True)
        return None


def parse_location(location_str: str) -> dict[str, Any] | None:
    """
    Parse location string "lng,lat" to GeoJSON Point format

    Args:
        location_str: Location string in format "lng,lat"

    Returns:
        Dict in GeoJSON Point format: {"type": "Point", "coordinates": [lng, lat]}
    """
    if not location_str:
        return None

    try:
        parts = location_str.split(",")
        if len(parts) != 2:
            return None

        lng = float(parts[0].strip())
        lat = float(parts[1].strip())

        return {
            "type": "Point",
            "coordinates": [lng, lat],
        }
    except (ValueError, IndexError) as e:
        logger.warning(f"Location parsing failed {location_str}: {e}")
        return None


def convert_to_attraction(
    attraction_data: dict[str, Any],
    images: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Convert JSON data to Attraction object

    Args:
        attraction_data: Attraction JSON data
        images: List of image File objects

    Returns:
        Attraction object dict
    """
    # Parse address
    address = {
        "country": "China",
        "province": attraction_data.get("pname", ""),
        "city": attraction_data.get("cityname", ""),
        "county": attraction_data.get("adname", ""),
        "district": "",  # No district field in JSON
        "street": attraction_data.get("address", ""),
    }

    # Parse location
    location = parse_location(attraction_data.get("location", ""))

    # Build Attraction object (don't set _id, let MongoDB generate ObjectId)
    attraction = {
        "name": attraction_data.get("name", ""),
        "address": address,
        "introduction": attraction_data.get("business", {}).get("rectag", ""),
        "tags": [],
        "images": images,
        "location": location,
    }

    # Process tags (extract from type field)
    type_str = attraction_data.get("type", "")
    if type_str:
        tags = [tag.strip() for tag in type_str.split(";") if tag.strip()]
        attraction["tags"] = tags

    return attraction


def process_attraction_images(
    attraction_data: dict[str, Any],
    mongo_id: str,
    grpc_client: file_pb2_grpc.FileServiceStub,
    http_client: httpx.Client,
) -> list[str]:
    """
    Process image upload for single attraction, using MongoDB ObjectId as path

    Args:
        attraction_data: Attraction JSON data
        mongo_id: MongoDB ObjectId
        grpc_client: gRPC client
        http_client: HTTP client

    Returns:
        List of successfully uploaded image paths
    """
    attraction_id = attraction_data.get("id")
    if not attraction_id:
        logger.warning("Attraction data missing id field")
        return []

    logger.info(
        f"Uploading attraction images: {attraction_data.get('name')}"
        f" (MongoDB ID: {mongo_id})"
    )

    # Read image directory (still use original id as directory name)
    image_dir = PICTURES_DIR / attraction_id
    if not image_dir.exists():
        logger.warning(f"Image directory does not exist: {image_dir}")
        return []

    # Get all image files (sorted by filename)
    image_files = sorted(image_dir.glob("*.*"))
    if not image_files:
        logger.warning(f"Image directory is empty: {image_dir}")
        return []

    # Upload all images (use MongoDB ObjectId as attraction_id in path)
    uploaded_image_paths = []
    for idx, image_path in enumerate[Any](image_files):
        file_info = upload_image(
            grpc_client,
            http_client,
            image_path,
            mongo_id,  # Use MongoDB ObjectId as path
            idx,
        )
        if file_info and file_info.get("path"):
            # Construct correct path format: 
            # permanent/{service}/attractions/{mongo_id}/{file_name}
            server_path = file_info["path"]
            if server_path.startswith("permanent/"):
                # If server already returns complete path, use it directly
                final_path = server_path
            else:
                # Manually construct complete path
                file_name = f"{mongo_id}_{idx}{image_path.suffix.lower()}"
                final_path = f"permanent/{SERVICE_NAME_OF_FILE}/attractions/{mongo_id}/{file_name}"

            uploaded_image_paths.append(final_path)
            logger.info(f"Image path: {final_path}")

    logger.info(
        f"✓ Attraction {attraction_data.get('name')} image upload completed,"
        f" {len(uploaded_image_paths)} images"
    )
    return uploaded_image_paths


def save_to_mongodb(
    attractions: list[dict[str, Any]],
    original_data: list[dict[str, Any]],
    collection: Collection[dict[str, Any]],
) -> dict[str, str]:
    """
    Save attractions to MongoDB

    Args:
        attractions: List of processed attractions
        original_data: List of original attraction data (for getting original IDs)
        collection: MongoDB collection

    Returns:
        Mapping dict: original attraction ID -> MongoDB ObjectId
    """
    if not attractions:
        logger.warning("No attractions to save")
        return {}

    if len(attractions) != len(original_data):
        logger.error("Attraction data and original data length mismatch")
        return {}

    logger.info(f"Saving {len(attractions)} attractions to MongoDB...")

    id_mapping = {}
    for i, attraction in enumerate[dict[str, Any]](attractions):
        # Generate new ObjectId
        mongo_id = ObjectId()
        attraction["_id"] = mongo_id

        # Establish mapping relationship
        original_id = original_data[i].get("id")
        if original_id:
            id_mapping[str(original_id)] = str(mongo_id)
            logger.info(f"Mapping: {original_id} -> {mongo_id}")

    # Use bulk_write for batch insertion
    operations = []
    for attraction in attractions:
        operations.append(InsertOne(attraction))

    result = collection.bulk_write(operations)

    logger.info(f"✓ MongoDB save completed: inserted {result.inserted_count} documents")

    return id_mapping


def main() -> None:
    """Main function"""
    logger.info("Starting attraction data import...")

    # Check if files exist
    if not JSON_FILE.exists():
        logger.error(f"JSON file does not exist: {JSON_FILE}")
        return

    if not PICTURES_DIR.exists():
        logger.error(f"Pictures directory does not exist: {PICTURES_DIR}")
        return

    # Read JSON file
    logger.info(f"Reading JSON file: {JSON_FILE}")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        attractions_data = json.load(f)

    logger.info(f"Read {len(attractions_data)} attraction data entries")

    # Connect to gRPC service
    logger.info(f"Connecting to file-service gRPC: {FILE_SERVICE_GRPC_ADDRESS}")
    try:
        grpc_channel = grpc.insecure_channel(FILE_SERVICE_GRPC_ADDRESS)
        # Wait for channel to be ready
        grpc.channel_ready_future(grpc_channel).result(timeout=10)
        grpc_client = file_pb2_grpc.FileServiceStub(grpc_channel)
        logger.info("✓ gRPC connection successful")
    except Exception as e:
        logger.error(f"gRPC connection failed: {e}")
        raise

    # Create HTTP client
    http_client = httpx.Client(timeout=30.0)

    try:
        # Connect to MongoDB
        logger.info(f"\nConnecting to MongoDB: {MONGO_URI}")
        try:
            mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            mongo_client.server_info()
            db = mongo_client[MONGO_DATABASE]
            collection = db[MONGO_COLLECTION]

            # Create index
            collection.create_index([("location", "2dsphere")])

            logger.info("✓ MongoDB connection successful")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

        # Process each attraction
        processed_attractions = []
        successful_data = []  # Save successfully processed attraction data for mapping

        for idx, attraction_data in enumerate(attractions_data, 1):
            logger.info(f"\n[{idx}/{len(attractions_data)}] Processing attraction...")

            # Check attraction data and image directory
            attraction_id = attraction_data.get("id")
            if not attraction_id:
                logger.warning("Attraction data missing id field")
                continue

            # Read image directory
            image_dir = PICTURES_DIR / attraction_id
            if not image_dir.exists():
                logger.warning(f"Image directory does not exist: {image_dir}")
                continue

            # Get all image files (sorted by filename)
            image_files = sorted(image_dir.glob("*.*"))
            if not image_files:
                logger.warning(f"Image directory is empty: {image_dir}")
                continue

            # Convert to Attraction object (no image info yet)
            attraction = convert_to_attraction(attraction_data, [])
            if not attraction:
                continue

            processed_attractions.append(attraction)
            successful_data.append(attraction_data)

        # First save attractions to MongoDB, get ObjectId
        id_mapping = save_to_mongodb(processed_attractions, successful_data, collection)

        # Now upload images using MongoDB ObjectId as path
        if id_mapping:
            logger.info("\nUploading images using MongoDB ObjectId as path...")

            for idx, (original_id, mongo_id) in enumerate(id_mapping.items()):
                # Find corresponding original data
                original_data = next(
                    (
                        item
                        for item in successful_data
                        if str(item.get("id")) == original_id
                    ),
                    None,
                )
                if not original_data:
                    continue

                logger.info(
                    f"[{idx + 1}/{len(id_mapping)}] Uploading attraction "
                    f"images: {original_data.get('name')}"
                )

                # Upload images using MongoDB ObjectId
                images = process_attraction_images(
                    original_data,
                    mongo_id,
                    grpc_client,
                    http_client
                )

                if images:
                    logger.info(f"Updating image paths: {images}")

                    # Update image information in MongoDB
                    result = collection.update_one(
                        {"_id": ObjectId(mongo_id)}, {"$set": {"images": images}}
                    )
                    if result.modified_count > 0:
                        logger.info(
                            f"✓ Attraction image info update successful: {original_data.get('name')}"
                            f" ({result.modified_count} documents modified)"
                        )
                    else:
                        logger.warning(
                            f"Attraction image info update failed: {original_data.get('name')}"
                            f" ({result.modified_count} documents modified)"
                        )
                else:
                    logger.warning(f"Image upload failed: {original_data.get('name')}")

        # Save mapping relationship to JSON file
        if id_mapping:
            mapping_file = SCRIPT_DIR / "id_mapping.json"
            logger.info(f"Saving ID mapping to: {mapping_file}")
            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(id_mapping, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Mapping file saved, {len(id_mapping)} mappings")

        # Close connection
        mongo_client.close()

        logger.info(
            f"\n✓ Import completed! Successfully processed {len(processed_attractions)} attractions"
        )

    except Exception as e:
        logger.error(f"Error occurred during processing: {e}", exc_info=True)
        raise

    finally:
        # Clean up resources
        http_client.close()
        grpc_channel.close()


if __name__ == "__main__":
    main()
