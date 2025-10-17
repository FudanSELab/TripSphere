import logging
from importlib.metadata import PackageNotFoundError, version

import grpc
from tripsphere.itinerary import metadata_pb2, metadata_pb2_grpc

logger = logging.getLogger(__name__)


class MetadataServiceServicer(metadata_pb2_grpc.MetadataServiceServicer):
    async def GetVersion(
        self,
        request: metadata_pb2.GetVersionRequest,
        context: grpc.aio.ServicerContext[
            metadata_pb2.GetVersionRequest, metadata_pb2.GetVersionResponse
        ],
    ) -> metadata_pb2.GetVersionResponse:
        try:
            _version = version("itinerary-planner")
        except PackageNotFoundError:
            logger.error("Package 'itinerary-planner' is not found")
            await context.abort(
                grpc.StatusCode.INTERNAL,
                "Required package 'itinerary-planner' is not installed",
            )
        logger.info(f"{self.GetVersion.__name__} returns version {_version}")
        return metadata_pb2.GetVersionResponse(version=_version)

