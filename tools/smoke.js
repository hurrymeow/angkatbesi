// Loads the app in headless Chromium and fails on page errors or a blank body.
const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2] || 'http://localhost:8080/';
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(url, { waitUntil: 'networkidle' });
  const text = (await page.innerText('body')).trim();
  await browser.close();
  if (errors.length) { console.error('Console/page errors:\n' + errors.join('\n')); process.exit(1); }
  if (!text) { console.error('Body is empty'); process.exit(1); }
  console.log('Smoke OK');
})();
