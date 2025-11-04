import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "minotar.net",
        pathname: "/avatar/**",
      },
    ],
  },
};

export default nextConfig;
