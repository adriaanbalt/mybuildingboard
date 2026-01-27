#!/usr/bin/env node

/**
 * Next.js HTTPS Server Wrapper
 *
 * Creates an HTTPS server that proxies to Next.js HTTP dev server
 * Uses certificates from certificates/ directory
 */

const https = require('https')
const http = require('http')
const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')

const HTTPS_PORT = 3000
const HTTP_PORT = 3001 // Next.js will run on this port internally

// Load certificates
const certPath = path.join(process.cwd(), 'certificates/localhost.pem')
const keyPath = path.join(process.cwd(), 'certificates/localhost-key.pem')

if (!fs.existsSync(certPath) || !fs.existsSync(keyPath)) {
  console.error('❌ SSL certificates not found!')
  console.error(`   Expected: ${certPath}`)
  console.error(`   Expected: ${keyPath}`)
  console.error(
    '   Run: openssl req -x509 -newkey rsa:4096 -keyout certificates/localhost-key.pem -out certificates/localhost.pem -days 365 -nodes -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1,IP:::1"'
  )
  process.exit(1)
}

const cert = fs.readFileSync(certPath)
const key = fs.readFileSync(keyPath)

// Start Next.js dev server on internal HTTP port
console.log('🚀 Starting Next.js dev server on HTTP port', HTTP_PORT)
const nextProcess = spawn('npx', ['next', 'dev', '-p', HTTP_PORT.toString()], {
  stdio: 'inherit',
  env: {
    ...process.env,
    PORT: HTTP_PORT.toString(),
  },
})

nextProcess.on('error', (error) => {
  console.error('❌ Failed to start Next.js:', error.message)
  process.exit(1)
})

// Wait a bit for Next.js to start, then create HTTPS proxy
setTimeout(() => {
  const server = https.createServer({ cert, key }, (req, res) => {
    const options = {
      hostname: '127.0.0.1',
      port: HTTP_PORT,
      path: req.url,
      method: req.method,
      headers: {
        ...req.headers,
        host: `127.0.0.1:${HTTP_PORT}`,
      },
    }

    const proxyReq = http.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers)
      proxyRes.pipe(res)
    })

    proxyReq.on('error', (error) => {
      console.error('❌ Proxy error:', error.message)
      if (!res.headersSent) {
        res.writeHead(502, { 'Content-Type': 'text/plain' })
        res.end('Bad Gateway: Unable to connect to Next.js')
      }
    })

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
    nextProcess.kill()
    process.exit(1)
  })

  server.listen(HTTPS_PORT, '127.0.0.1', () => {
    console.log('')
    console.log('╭─────────────────────────────────────────────────────────╮')
    console.log('│ 🔒 Next.js HTTPS Server                                  │')
    console.log('├─────────────────────────────────────────────────────────┤')
    console.log(`│ HTTPS: https://localhost:${HTTPS_PORT}                    │`)
    console.log(`│ HTTP:  http://127.0.0.1:${HTTP_PORT} (internal)          │`)
    console.log('╰─────────────────────────────────────────────────────────╯')
    console.log('')
    console.log('✅ HTTPS server is running')
    console.log('')
  })

  // Graceful shutdown
  const shutdown = () => {
    console.log('\n🛑 Shutting down...')
    server.close(() => {
      nextProcess.kill()
      process.exit(0)
    })
  }

  process.on('SIGINT', shutdown)
  process.on('SIGTERM', shutdown)
}, 3000) // Wait 3 seconds for Next.js to start
