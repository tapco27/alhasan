// Captures the company site as a phone would show it: the whole page (lazy images loaded) and the fixed bottom bar separately.
// Usage: node site_shot.mjs <url> <outDir>
import { createRequire } from 'node:module';
const { chromium, devices } = createRequire(import.meta.url)('playwright');
const [url, outDir] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await (await browser.newContext({ ...devices['iPhone 14 Pro'], locale: 'ar' })).newPage();
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
await page.waitForTimeout(3000);

// Scroll through the page so lazy images load, then return to the top
const h = await page.evaluate(() => document.documentElement.scrollHeight);
for (let y = 0; y < h; y += 500) { await page.evaluate(v => window.scrollTo(0, v), y); await page.waitForTimeout(350); }
await page.evaluate(() => Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 8000); }))));
await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(800);

// Fixed bars: shoot the bottom one on its own, hide all of them for the tall capture
const fixed = await page.evaluate(() => [...document.querySelectorAll('body *')].filter(e => { const s = getComputedStyle(e); return (s.position === 'fixed' || s.position === 'sticky') && e.offsetHeight > 30 && e.offsetHeight < 200; })
  .map((e, i) => { e.dataset.fx = i; const r = e.getBoundingClientRect(); return { i, top: r.top, h: r.height, pos: getComputedStyle(e).position }; }));
console.log('fixed', JSON.stringify(fixed));
const bottom = fixed.filter(f => f.pos === 'fixed' && f.top > 500).sort((a, b) => b.h - a.h)[0];
if (bottom) await page.locator(`[data-fx="${bottom.i}"]`).screenshot({ path: `${outDir}/nav.png` });
await page.addStyleTag({ content: fixed.filter(f => f.pos === 'fixed').map(f => `[data-fx="${f.i}"]{display:none!important}`).join('') });
await page.screenshot({ path: `${outDir}/full.jpg`, fullPage: true, type: 'jpeg', quality: 90 });
// The sticky header, to pin at the top of the phone screen while the page scrolls
await page.screenshot({ path: `${outDir}/head.png`, clip: { x: 0, y: 0, width: 393, height: 82 } });

// Where things are (CSS px), so the film can scroll to the first project and tap its button
const marks = await page.evaluate(() => {
  const btn = [...document.querySelectorAll('a')].find(a => a.textContent.trim().startsWith('عرض المشروع')), r = btn?.getBoundingClientRect();
  const img = [...document.images].find(i => i.naturalWidth > 1000 && i.getBoundingClientRect().top > 300)?.getBoundingClientRect();
  return { width: innerWidth, height: document.documentElement.scrollHeight, firstImageTop: img?.top + scrollY, button: r && { x: r.left + r.width / 2, y: r.top + scrollY + r.height / 2 } };
});
console.log('marks', JSON.stringify(marks));
(await import('node:fs')).writeFileSync(`${outDir}/marks.json`, JSON.stringify(marks));
await browser.close();
