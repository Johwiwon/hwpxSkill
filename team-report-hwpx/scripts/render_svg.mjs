#!/usr/bin/env node
// HWPX/HWP 각 쪽을 SVG 로 그린다(동봉한 rhwp WASM, MIT).
//   node render_svg.mjs 입력.hwpx 출력폴더
// 글꼴이 없는 환경에서는 대체 글꼴로 그려지고, 한글 레이아웃 캐시가 없는 파일은
// 빈 문단 간격이 넓게 그려진다. 쪽 배치·표 모양 확인용이다.
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const RHWP = path.join(path.dirname(url.fileURLToPath(import.meta.url)), "..", "vendor", "rhwp");

function estimateTextWidth(font, text) {
  const match = String(font ?? "").match(/([0-9.]+)px/);
  const size = match ? Number.parseFloat(match[1]) : 12;
  let width = 0;
  for (const ch of String(text ?? "")) {
    const cp = ch.codePointAt(0) ?? 0;
    width += cp >= 0x1100 && cp <= 0xffdc ? size : ch === " " ? size * 0.45 : size * 0.5;
  }
  return width;
}

const [input, outDir] = process.argv.slice(2);
if (!input || !outDir) {
  console.error("usage: node render_svg.mjs <input.hwpx|hwp> <outDir>");
  process.exit(2);
}
globalThis.measureTextWidth = estimateTextWidth;
const rhwp = await import(url.pathToFileURL(path.join(RHWP, "rhwp.js")).href);
await rhwp.default({ module_or_path: fs.readFileSync(path.join(RHWP, "rhwp_bg.wasm")) });
const doc = new rhwp.HwpDocument(new Uint8Array(fs.readFileSync(input)));
fs.mkdirSync(outDir, { recursive: true });
const n = doc.pageCount();
for (let i = 0; i < n; i += 1) {
  fs.writeFileSync(path.join(outDir, `page${String(i + 1).padStart(2, "0")}.svg`), doc.renderPageSvg(i));
}
console.log(`pages: ${n}`);
