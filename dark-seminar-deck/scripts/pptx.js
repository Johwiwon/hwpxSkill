// usage: NODE_PATH=<node_modules> node pptx.js <shotsDir> <out.pptx> [notes.json] [title] [author]
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');
const [shots, out, notesPath, title, author] = process.argv.slice(2);
const notes = notesPath && fs.existsSync(notesPath) ? JSON.parse(fs.readFileSync(notesPath, 'utf8')) : [];
const files = fs.readdirSync(shots).filter(f => /^s\d+\.png$/.test(f))
  .sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1)));
const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = title || '발표자료';
if (author) pres.author = author;
files.forEach((f, i) => {
  const slide = pres.addSlide();
  slide.background = { color: '090E1B' };
  const png = fs.readFileSync(path.join(shots, f));
  slide.addImage({ data: 'image/png;base64,' + png.toString('base64'), x: 0, y: 0, w: 10, h: 5.625, altText: `slide ${i + 1}` });
  if (notes[i]) slide.addNotes(notes[i]);
});
pres.writeFile({ fileName: out }).then(f => console.log('wrote', f));
