// usage: node _build/build.mjs   → ../index.html
//   src.html 의 자리표시를 채운다.
//   <i data-icon="lucide-이름"></i>     → 인라인 SVG 아이콘 (lucide-static)
//   <div class="plotbox" data-chart='{...}'></div> → 막대 차트 (아래 chart() 참고)
//   {{WAVE}}                             → 표지 파형 SVG
//   {{N}} / {{P}}                        → 쪽 번호 "03 / 18", 진행 막대 폭 %
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const here = path.dirname(new URL(import.meta.url).pathname);
const OUT = path.join(here, '..', 'index.html');
const TOOLS = process.env.DECK_TOOLS || path.join(os.homedir(), '.cache', 'dark-seminar-deck');
const ICONS = process.env.ICONS || path.join(TOOLS, 'node_modules/lucide-static/icons');
let html = fs.readFileSync(path.join(here, 'src.html'), 'utf8');

// 묶음 막대 차트. 값 옆에 숫자를 직접 적는다(범례만 보고 읽게 하지 않는다).
// data-chart 예: {"max":40,"step":10,"height":420,"barW":120,
//   "groups":[{"cat":"영어","vals":[[32.2,"A"],[33.1,"B"]]}]}   ← "A"/"B"/"C" = 계열 색(--sA/--sB/--sC)
//   "unit":"%" 를 주면 막대 위 값 뒤에 단위를 붙인다. 계열이 하나면 vals 에 값 하나만 넣는다(범례는 빼도 된다).
function chart({ max, step, height = 420, barW = 110, unit = '', groups }) {
  const color = c => (/^[ABC]$/.test(c) ? `var(--s${c})` : c);
  let grid = '';
  for (let v = 0; v <= max; v += step)
    grid += `<div class="gl${v === 0 ? ' base' : ''}" style="bottom:${(v / max * 100).toFixed(2)}%"><span>${v}</span></div>`;
  const gs = groups.map(g => `<div class="grp">${g.vals.map(([v, c]) =>
    `<div class="bar" style="width:${barW}px;height:${(v / max * 100).toFixed(2)}%;background:${color(c)}"><b>${v}${unit}</b></div>`).join('')}<span class="cat">${g.cat}</span></div>`).join('');
  return `<div class="plot" style="height:${height}px">${grid}<div class="groups">${gs}</div></div>`;
}
html = html.replace(/<div class="plotbox" data-chart='([^']*)'><\/div>/g, (_, json) => chart(JSON.parse(json)));

// lucide 아이콘 → 인라인 svg
const missing = new Set();
html = html.replace(/<i( class="[^"]*")? data-icon="([a-z0-9-]+)"([^>]*)><\/i>/g, (_, cls, name, rest) => {
  const f = path.join(ICONS, name + '.svg');
  if (!fs.existsSync(f)) { missing.add(name); return ''; }
  let svg = fs.readFileSync(f, 'utf8').replace(/<!--.*?-->/s, '').replace(/\s*\n\s*/g, ' ').trim();
  const extra = cls ? cls.match(/"([^"]*)"/)[1] : '';
  svg = svg.replace(/class="[^"]*"/, `class="ic${extra ? ' ' + extra : ''}"`).replace(/ width="24" height="24"/, '');
  const style = rest.match(/style="([^"]*)"/);
  if (style) svg = svg.replace('<svg ', `<svg style="${style[1]}" `);
  return svg;
});
if (missing.size) { console.error('없는 아이콘:', [...missing].join(', '), '\n  → https://lucide.dev/icons 에서 이름 확인'); process.exit(1); }

// 표지 파형 (고정 시드라 빌드할 때마다 같은 모양)
function wave() {
  const n = 56, w = 552, h = 130, gap = 4, bw = (w - gap * (n - 1)) / n;
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  let bars = '';
  for (let i = 0; i < n; i++) {
    const env = 0.35 + 0.65 * Math.sin(Math.PI * (i + 0.5) / n) * (0.6 + 0.4 * Math.sin(i / 2.7));
    const bh = Math.max(10, h * env * (0.45 + 0.55 * rnd()));
    bars += `<rect x="${(i * (bw + gap)).toFixed(1)}" y="${((h - bh) / 2).toFixed(1)}" width="${bw.toFixed(1)}" height="${bh.toFixed(1)}" rx="${(bw / 2).toFixed(1)}"/>`;
  }
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}"><defs><linearGradient id="wg" x1="0" x2="1"><stop offset="0" stop-color="#7DD3FC"/><stop offset=".5" stop-color="#0EA5E9"/><stop offset="1" stop-color="#A78BFA"/></linearGradient></defs><g fill="url(#wg)">${bars}</g></svg>`;
}
html = html.replace('{{WAVE}}', wave());

// 쪽 번호 + 진행 막대
const parts = html.split('<section class="slide');
const total = parts.length - 1;
html = parts.map((p, i) => i === 0 ? p :
  p.replace('{{N}}', `${String(i).padStart(2, '0')} / ${String(total).padStart(2, '0')}`)
   .replace('{{P}}', `${(i / total * 100).toFixed(2)}%`)).join('<section class="slide');

fs.writeFileSync(OUT, html);
console.log('wrote', OUT, total, 'slides');
