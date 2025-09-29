import logging
from importlib.metadata import PackageNotFoundError, version

import grpc
from tripsphere.itinerary import metadata_pb2, metadata_pb2_grpc

logger = logging.getLogger(__name__)


class MetadataServiceServicer(metadata_pb2_grpc.MetadataServiceServicer):
    def GetVersion(
        self, request: metadata_pb2.GetVersionRequest, context: grpc.ServicerContext
    ) -> metadata_pb2.GetVersionResponse:
        try:
            _version = version("itinerary")
        except PackageNotFoundError:
            logger.error("Package 'itinerary' is not found")
            context.abort(
                grpc.StatusCode.INTERNAL,
                "Required package 'itinerary' is not installed",
            )
        logger.info(f"{self.GetVersion.__name__} returns version {_version}")
        return metadata_pb2.GetVersionResponse(version=_version)
