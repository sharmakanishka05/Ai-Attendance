/** @type {import('next').NextConfig} */
const getBackendUrl = () => {
  const envBackend =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    (process.env.NEXT_PUBLIC_API_URL && !process.env.NEXT_PUBLIC_API_URL.startsWith('/')
      ? process.env.NEXT_PUBLIC_API_URL
      : null) ||
    'http://127.0.0.1:8000';

  return envBackend.replace(/\/+$/, '').replace(/\/api$/, '');
};

const backendDestination = `${getBackendUrl()}/api/:path*`;

const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: backendDestination,
      },
    ];
  },
};

export default nextConfig;
