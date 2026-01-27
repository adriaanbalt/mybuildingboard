#!/usr/bin/env node

/**
 * Supabase HTTPS Proxy
 *
 * Proxies HTTPS requests (port 54421) to Supabase HTTP backend (port 54321)
 * Required for OAuth integrations that require HTTPS
 */

const https = require('https')
const http = require('http')
const fs = require('fs')
const path = require('path')

const HTTPS_PORT = 54421
const HTTP_PORT = 54321
const TARGET_HOST = '127.0.0.1'

// Try to find SSL certificates
const certPaths = [
  path.join(__dirname, '../../infrastructure/certs/localhost+2.pem'),
  path.join(__dirname, '../../infrastructure/certs/cert.pem'),
  path.join(process.cwd(), 'infrastructure/certs/localhost+2.pem'),
  path.join(process.cwd(), 'infrastructure/certs/cert.pem'),
]

let cert, key

// Try to load certificates
for (const certPath of certPaths) {
  const keyPath = certPath.replace(/\.pem$/, '-key.pem').replace(/cert\.pem$/, 'key.pem')

  if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
    try {
      cert = fs.readFileSync(certPath)
      key = fs.readFileSync(keyPath)
      console.log(`✅ Loaded SSL certificates from: ${certPath}`)
      break
    } catch (error) {
      console.warn(`⚠️  Failed to load certificates from ${certPath}:`, error.message)
    }
  }
}

// If no certificates found, create a self-signed certificate for development
if (!cert || !key) {
  console.warn('⚠️  No SSL certificates found. Using self-signed certificate for development.')
  console.warn('   For production-like setup, run: bash scripts/utils/dev/setup-local-https.sh')

  // Generate a simple self-signed cert (Node.js 18+ has built-in support)
  // For now, we'll use a workaround with a minimal cert
  const { execSync } = require('child_process')

  try {
    // Try to use mkcert if available
    const certDir = path.join(process.cwd(), 'infrastructure/certs')
    if (!fs.existsSync(certDir)) {
      fs.mkdirSync(certDir, { recursive: true })
    }

    const certFile = path.join(certDir, 'localhost+2.pem')
    const keyFile = path.join(certDir, 'localhost+2-key.pem')

    if (!fs.existsSync(certFile) || !fs.existsSync(keyFile)) {
      console.log('📝 Generating self-signed certificate...')
      // Use openssl to generate a self-signed cert
      execSync(
        `openssl req -x509 -newkey rsa:4096 -keyout "${keyFile}" -out "${certFile}" -days 365 -nodes -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1" 2>/dev/null || true`,
        { stdio: 'ignore' }
      )
    }

    if (fs.existsSync(certFile) && fs.existsSync(keyFile)) {
      cert = fs.readFileSync(certFile)
      key = fs.readFileSync(keyFile)
      console.log('✅ Generated self-signed certificate')
    }
  } catch (error) {
    // If openssl fails, we'll proceed without SSL (will fail, but user will see error)
    console.error('❌ Failed to generate certificate. Please install mkcert or openssl.')
    console.error('   Run: bash scripts/utils/dev/setup-local-https.sh')
  }
}

if (!cert || !key) {
  console.error('❌ No SSL certificates available. Cannot start HTTPS proxy.')
  console.error('   Please run: bash scripts/utils/dev/setup-local-https.sh')
  process.exit(1)
}

// Create HTTPS server that proxies to HTTP backend
const server = https.createServer({ cert, key }, (req, res) => {
  const options = {
    hostname: TARGET_HOST,
    port: HTTP_PORT,
    path: req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: `${TARGET_HOST}:${HTTP_PORT}`,
    },
  }

  const proxyReq = http.request(options, (proxyRes) => {
    // Copy response headers
    res.writeHead(proxyRes.statusCode, proxyRes.headers)

    // Pipe response
    proxyRes.pipe(res)
  })

  proxyReq.on('error', (error) => {
    console.error('❌ Proxy error:', error.message)
    if (!res.headersSent) {
      res.writeHead(502, { 'Content-Type': 'text/plain' })
      res.end('Bad Gateway: Unable to connect to Supabase backend')
    }
  })

  // Pipe request body
  req.pipe(proxyReq)
})

server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error(`❌ Port ${HTTPS_PORT} is already in use.`)
    console.error(`   Stop the existing process or use a different port.`)
    console.error(`   Check: lsof -ti:${HTTPS_PORT}`)
  } else {
    console.error('❌ Server error:', error.message)
  }
  process.exit(1)
})

server.listen(HTTPS_PORT, '127.0.0.1', () => {
  console.log('')
  console.log('╭─────────────────────────────────────────────────────────╮')
  console.log('│ 🔒 Supabase HTTPS Proxy                                  │')
  console.log('├─────────────────────────────────────────────────────────┤')
  console.log(`│ Listening on: https://127.0.0.1:${HTTPS_PORT}              │`)
  console.log(`│ Proxying to:  http://127.0.0.1:${HTTP_PORT}               │`)
  console.log('╰─────────────────────────────────────────────────────────╯')
  console.log('')
  console.log('✅ HTTPS proxy is running')
  console.log(`   Use: NEXT_PUBLIC_SUPABASE_URL=https://127.0.0.1:${HTTPS_PORT}`)
  console.log('')
})

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down HTTPS proxy...')
  server.close(() => {
    console.log('✅ HTTPS proxy stopped')
    process.exit(0)
  })
})

process.on('SIGTERM', () => {
  server.close(() => {
    process.exit(0)
  })
})
