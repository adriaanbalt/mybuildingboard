/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
  // Environment variables that should be available to the client
  env: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  },
  webpack: (config, { isServer }) => {
    // Fix for @supabase/ssr module resolution
    // The package doesn't have dist/index.mjs, webpack tries to resolve it incorrectly
    // Use the correct entry point based on environment
    const path = require('path')
    
    config.resolve.alias = {
      ...config.resolve.alias,
      '@supabase/ssr': path.resolve(
        __dirname,
        'node_modules/@supabase/ssr',
        isServer ? 'dist/main/index.js' : 'dist/module/index.js'
      ),
    }
    
    return config
  },
}

module.exports = nextConfig
