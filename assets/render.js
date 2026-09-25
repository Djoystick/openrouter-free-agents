const path = require('path');
const fs = require('fs');

// Use puppeteer-core from Site_Slepa4ok
const puppeteer = require('h:\\Work\\Site_Slepa4ok\\node_modules\\puppeteer-core');

function findBrowser() {
  const candidates = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe'),
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
  ];
  for (const c of candidates) {
    if (c && fs.existsSync(c)) return c;
  }
  throw new Error('Chrome/Edge not found');
}

async function render() {
  const browserPath = findBrowser();
  const htmlPath = 'file:///' + path.resolve('h:\\Work\\openrouter-free-agents\\assets\\preview.html').replace(/\\/g, '/');
  const outPng = path.resolve('h:\\Work\\openrouter-free-agents\\assets\\social-preview.png');
  const artifactPng = path.resolve('C:\\Users\\Djoystick\\.gemini\\antigravity\\brain\\0b737243-3db0-4fc2-b99a-8b7033f5b4be\\social_preview_openrouter.png');

  console.log('Rendering from:', htmlPath);
  const browser = await puppeteer.launch({
    executablePath: browserPath,
    headless: 'new',
    defaultViewport: {
      width: 1280,
      height: 640,
      deviceScaleFactor: 2 // 2x Retina rendering for ultra crispness
    },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 640, deviceScaleFactor: 2 });
  await page.goto(htmlPath, { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await new Promise(r => setTimeout(r, 400));

  await page.screenshot({ path: outPng, type: 'png' });
  await page.screenshot({ path: artifactPng, type: 'png' });
  await browser.close();

  console.log('Saved social preview to:', outPng);
  console.log('Saved artifact to:', artifactPng);
}

render().catch(err => {
  console.error('Failed:', err);
  process.exit(1);
});
