const fs = require("fs");
const path = require("path");

const docsDir = __dirname;

const files = [
  "architecture-fonctionnelle.md",
  "architecture-reseau.md",
  "architecture-technique.md",
];

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inline(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function tableToHtml(rows) {
  const cells = rows.map((row) =>
    row
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => inline(cell.trim()))
  );

  if (cells.length < 2) return "";
  const head = cells[0].map((cell) => `<th>${cell}</th>`).join("");
  const body = cells
    .slice(2)
    .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
    .join("\n");
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function markdownToHtml(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let paragraph = [];
  let list = [];
  let table = [];
  let inCode = false;
  let codeLang = "";
  let code = [];

  function flushParagraph() {
    if (!paragraph.length) return;
    out.push(`<p>${inline(paragraph.join(" "))}</p>`);
    paragraph = [];
  }

  function flushList() {
    if (!list.length) return;
    out.push(`<ul>${list.map((item) => `<li>${inline(item)}</li>`).join("")}</ul>`);
    list = [];
  }

  function flushTable() {
    if (!table.length) return;
    out.push(tableToHtml(table));
    table = [];
  }

  function flushCode() {
    if (codeLang === "mermaid") {
      out.push(`<div class="mermaid">${escapeHtml(code.join("\n"))}</div>`);
    } else {
      out.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
    }
    code = [];
    codeLang = "";
  }

  for (const line of lines) {
    const codeStart = line.match(/^```(\w+)?/);
    if (codeStart) {
      if (inCode) {
        flushCode();
        inCode = false;
      } else {
        flushParagraph();
        flushList();
        flushTable();
        inCode = true;
        codeLang = codeStart[1] || "";
      }
      continue;
    }

    if (inCode) {
      code.push(line);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      flushList();
      flushTable();
      continue;
    }

    if (/^\|.*\|$/.test(line.trim())) {
      flushParagraph();
      flushList();
      table.push(line);
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      flushParagraph();
      flushList();
      flushTable();
      const level = heading[1].length;
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      continue;
    }

    const bullet = line.match(/^-\s+(.*)$/);
    if (bullet) {
      flushParagraph();
      flushTable();
      list.push(bullet[1]);
      continue;
    }

    flushList();
    flushTable();
    paragraph.push(line.trim());
  }

  flushParagraph();
  flushList();
  flushTable();
  if (inCode) flushCode();
  return out.join("\n");
}

function htmlPage(title, body) {
  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    @page { size: A4; margin: 14mm; }
    body {
      font-family: "Segoe UI", Arial, sans-serif;
      color: #102033;
      line-height: 1.42;
      font-size: 11px;
    }
    h1 {
      color: #082653;
      font-size: 24px;
      border-bottom: 3px solid #0a58ca;
      padding-bottom: 8px;
      margin: 0 0 18px;
    }
    h2 {
      color: #0a3f86;
      font-size: 16px;
      margin: 22px 0 9px;
      break-after: avoid;
    }
    h3, h4 {
      color: #0a3f86;
      font-size: 13px;
      margin: 16px 0 7px;
      break-after: avoid;
    }
    p { margin: 6px 0 10px; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0 16px;
      page-break-inside: avoid;
    }
    th {
      background: #eaf2ff;
      color: #082653;
      font-weight: 700;
    }
    th, td {
      border: 1px solid #b7c8de;
      padding: 6px 7px;
      vertical-align: top;
    }
    code {
      font-family: Consolas, "Courier New", monospace;
      background: #f1f5f9;
      padding: 1px 4px;
      border-radius: 3px;
    }
    pre {
      background: #0f172a;
      color: #e2e8f0;
      padding: 10px;
      border-radius: 6px;
      overflow: hidden;
      page-break-inside: avoid;
      white-space: pre-wrap;
    }
    .mermaid {
      display: block;
      margin: 10px auto 18px;
      text-align: center;
      page-break-inside: avoid;
      transform-origin: top center;
    }
    .page-break { page-break-before: always; }
  </style>
</head>
<body>
${body}
<script>
  mermaid.initialize({ startOnLoad: false, securityLevel: "loose", theme: "base" });
  window.addEventListener("load", async () => {
    try { await mermaid.run({ querySelector: ".mermaid" }); }
    finally { document.body.setAttribute("data-rendered", "true"); }
  });
</script>
</body>
</html>`;
}

for (const file of files) {
  const md = fs.readFileSync(path.join(docsDir, file), "utf8");
  const html = htmlPage(file.replace(".md", ""), markdownToHtml(md));
  fs.writeFileSync(path.join(docsDir, file.replace(".md", ".html")), html, "utf8");
}

const combinedBody = files
  .map((file, index) => {
    const md = fs.readFileSync(path.join(docsDir, file), "utf8");
    return `${index ? '<div class="page-break"></div>' : ""}${markdownToHtml(md)}`;
  })
  .join("\n");

fs.writeFileSync(
  path.join(docsDir, "architectures-deceptr.html"),
  htmlPage("Architectures DECEPTR v1 MVP", combinedBody),
  "utf8"
);
