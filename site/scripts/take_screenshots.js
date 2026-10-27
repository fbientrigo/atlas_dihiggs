import { chromium } from 'playwright';
import http from 'http';
import fs from 'fs';
import path from 'path';

const SHOTS_DIR = '/tmp/claude-1000/-home-fabian-atlas-dihiggs/33b1cf7c-4d0d-43f7-ba9c-c7109ff52f47/scratchpad/shots';
fs.mkdirSync(SHOTS_DIR, { recursive: true });

const DIST_DIR = '/home/fabian/atlas_dihiggs/site/dist';

// Simple static HTTP server
function serveStatic(req, res) {
  let reqPath = req.url.split('?')[0];
  if (reqPath.endsWith('/')) {
    reqPath += 'index.html';
  }
  let filePath = path.join(DIST_DIR, reqPath);
  if (!fs.existsSync(filePath)) {
    filePath = path.join(DIST_DIR, reqPath, 'index.html');
  }

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const contentTypes = {
      '.html': 'text/html',
      '.css': 'text/css',
      '.js': 'text/javascript',
      '.png': 'image/png',
      '.svg': 'image/svg+xml',
      '.json': 'application/json',
      '.wasm': 'application/wasm'
    };
    res.writeHead(200, { 'Content-Type': contentTypes[ext] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
}

const server = http.createServer(serveStatic);
server.listen(4321, async () => {
  console.log('[*] Static server running on http://localhost:4321');

  try {
    const browser = await chromium.launch();
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    // 1. Home
    console.log('[*] Capturing Home...');
    await page.goto('http://localhost:4321/', { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(SHOTS_DIR, 'home.png'), fullPage: false });
    console.log('[+] Saved home.png');

    // 2. C++ API Page
    console.log('[*] Capturing C++ API page...');
    await page.goto('http://localhost:4321/api/cpp/base/2hdmc/', { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(SHOTS_DIR, 'cpp_api.png'), fullPage: false });
    console.log('[+] Saved cpp_api.png');

    // 3. Python API Page
    console.log('[*] Capturing Python API page...');
    await page.goto('http://localhost:4321/api/python/dihiggs-boundary/', { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(SHOTS_DIR, 'python_api.png'), fullPage: false });
    console.log('[+] Saved python_api.png');

    await browser.close();
    console.log('[*] All 3 screenshots saved successfully.');
  } catch (err) {
    console.error('[!] Screenshot error:', err);
  } finally {
    server.close();
  }
});
