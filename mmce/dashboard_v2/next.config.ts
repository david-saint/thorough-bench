import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  basePath: '/thorough-bench',
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
