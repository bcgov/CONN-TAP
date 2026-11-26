/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  experimental: {
    serverActions: {
      allowedOrigins: ["**.telecomaccesspoint.gov.bc.ca"],
    },
  },
};

module.exports = nextConfig;
