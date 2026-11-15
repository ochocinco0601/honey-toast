# Measuring the text on a rendered page

Run this with the browser's evaluate_script in every state you walk (each step, tab, lens, open fold), at desktop and phone width, and in both light and dark themes when the page has both: a colour that passes on dark can fail on light. It lists every distinct text style on screen, with its rendered size (text inside a scaled drawing at the size it is actually shown), contrast against what is behind it, line height and characters per line, and flags small text, low contrast, tight lines and long lines. It covers web pages only. Its numbers are evidence for the review's questions; they do not replace looking.

It flags text below 12 px as rendered, contrast below 4.5:1 (3:1 for large text), a line height under 1.4 in running text, and lines over 80 characters.

```js

() => {
  const cv = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const parse = c => { if (!c || c === 'none' || c === 'transparent') return null; cv.clearRect(0, 0, 1, 1); cv.fillStyle = '#000'; cv.fillStyle = c; cv.fillRect(0, 0, 1, 1); const d = cv.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const bgOf = el => {
    for (let e = el; e; e = e.parentElement) {
      if (e instanceof SVGElement && e.tagName.toLowerCase() !== 'svg') { const f = parse(getComputedStyle(e).fill); if (e.tagName.toLowerCase() === 'rect' && f && (f.length < 4 || f[3] > 0.5)) return f.slice(0, 3); }
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c && (c.length < 4 || c[3] > 0.5)) return c.slice(0, 3);
    }
    const r = parse(getComputedStyle(document.documentElement).backgroundColor);
    return r && (r.length < 4 || r[3] > 0) ? r.slice(0, 3) : [255, 255, 255];
  };
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0.05; };
  const groups = new Map();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, { acceptNode: n => n.textContent.trim().length > 1 ? 1 : 2 });
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement; if (!el || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'TITLE'].includes(el.tagName) || !vis(el)) continue;
    const s = getComputedStyle(el), svg = el.closest('svg'), inSvg = !!svg;
    let size = parseFloat(s.fontSize);
    if (inSvg) { const vb = svg.viewBox && svg.viewBox.baseVal; if (vb && vb.width) size *= svg.getBoundingClientRect().width / vb.width; }
    const fill = inSvg ? parse(s.fill) : null;
    const fg = (fill && fill.length >= 3 ? fill : parse(s.color) || [0, 0, 0]).slice(0, 3);
    const cr = ratio(fg, bgOf(el));
    const lh = s.lineHeight === 'normal' ? null : parseFloat(s.lineHeight) / parseFloat(s.fontSize);
    let cpl = null;
    if (!inSvg && ['P', 'LI', 'DD', 'BLOCKQUOTE'].includes(el.tagName)) cpl = Math.round(el.getBoundingClientRect().width / (parseFloat(s.fontSize) * 0.5));
    const key = [el.tagName, inSvg, size.toFixed(1), s.fontWeight, cr.toFixed(2), lh ? lh.toFixed(2) : ''].join('|');
    const g = groups.get(key) || { tag: el.tagName.toLowerCase(), inSvg, px: +size.toFixed(1), weight: s.fontWeight, contrast: +cr.toFixed(2), lineHeight: lh ? +lh.toFixed(2) : null, charsPerLine: null, count: 0, sample: n.textContent.trim().slice(0, 50) };
    g.count++; if (cpl && cpl > (g.charsPerLine || 0)) g.charsPerLine = cpl;
    groups.set(key, g);
  }
  const rows = [...groups.values()];
  rows.forEach(r => { r.flags = [
    r.px < 12 ? 'small (<12px)' : '',
    r.contrast < ((r.px >= 24 || (r.px >= 18.66 && +r.weight >= 700)) ? 3 : 4.5) ? 'low contrast' : '',
    r.lineHeight && !r.inSvg && r.lineHeight < 1.4 && r.charsPerLine > 40 ? 'tight lines (<1.4)' : '',
    r.charsPerLine > 80 ? 'long lines (>80 chars)' : ''
  ].filter(Boolean); });
  rows.sort((a, b) => b.flags.length - a.flags.length || b.count - a.count);
  return { width: innerWidth, textStyles: rows.length, flagged: rows.filter(r => r.flags.length).slice(0, 25) };
}
```
