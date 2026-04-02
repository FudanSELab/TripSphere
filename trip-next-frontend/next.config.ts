import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: [
    "@copilotkit/runtime",
    "@grpc/grpc-js",
    "@bufbuild/protobuf",
  ],
};

export default nextConfig;
