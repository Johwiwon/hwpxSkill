#!/usr/bin/env node
// HWP(바이너리) 문서를 읽기용 HWPX 사본으로 바꾼다(동봉한 rhwp WASM, MIT).
//   node read_hwp.mjs 원본.hwp 사본.hwpx
// 원본은 건드리지 않는다. 사본은 내용 확인·텍스트 추출용이며, 사용자에게 보낼
// 결과물은 build_report.py 로 새로 만든다.
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const RHWP = path.join(path.dirname(url.fileURLToPath(import.meta.url)), "..", "vendor", "rhwp");
const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error("usage: node read_hwp.mjs <input.hwp> <output.hwpx>");
  process.exit(2);
}
const src = fs.readFileSync(input);
if (src[0] === 0x50 && src[1] === 0x4b) {
  console.error("이미 HWPX(ZIP) 파일입니다. 그대로 읽으면 됩니다.");
  process.exit(1);
}
globalThis.measureTextWidth = (font, text) => String(text ?? "").length * 12;
const rhwp = await import(url.pathToFileURL(path.join(RHWP, "rhwp.js")).href);
await rhwp.default({ module_or_path: fs.readFileSync(path.join(RHWP, "rhwp_bg.wasm")) });
const doc = new rhwp.HwpDocument(new Uint8Array(src));
try {
  fs.writeFileSync(output, doc.exportHwpx());
  console.log(`사본 생성: ${output}`);
} finally {
  doc.free();
}
