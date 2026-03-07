interface MarkdownReportProps {
  content: string;
}

/** Render a Markdown assessment report as styled HTML. */
export function MarkdownReport({
  content,
}: MarkdownReportProps): React.ReactElement {
  return (
    <div
      className="markdown-body"
      dangerouslySetInnerHTML={{ __html: markdownToHtml(content) }}
    />
  );
}

/**
 * Minimal Markdown→HTML converter for assessment reports.
 * Handles headings, tables, lists, code, bold, italic, links, blockquotes.
 */
function markdownToHtml(md: string): string {
  let html = md;

  // Escape HTML entities (but preserve our own tags later)
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks (```...```)
  html = html.replace(
    /```(\w*)\n([\s\S]*?)```/g,
    (_match, _lang, code) => `<pre><code>${code.trim()}</code></pre>`,
  );

  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Headings
  html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Links
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
  );

  // Tables
  html = html.replace(
    /^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)*)/gm,
    (_match: string, headerLine: string, _sepLine: string, bodyBlock: string) => {
      const headers = headerLine
        .split("|")
        .filter((c: string) => c.trim())
        .map((c: string) => `<th>${c.trim()}</th>`)
        .join("");
      const rows = bodyBlock
        .trim()
        .split("\n")
        .map((row: string) => {
          const cells = row
            .split("|")
            .filter((c: string) => c.trim())
            .map((c: string) => `<td>${c.trim()}</td>`)
            .join("");
          return `<tr>${cells}</tr>`;
        })
        .join("");
      return `<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
    },
  );

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>");

  // Unordered lists
  html = html.replace(
    /^((?:- .+\n?)+)/gm,
    (block: string) => {
      const items = block
        .trim()
        .split("\n")
        .map((line: string) => `<li>${line.replace(/^- /, "")}</li>`)
        .join("");
      return `<ul>${items}</ul>`;
    },
  );

  // Paragraphs — wrap remaining text lines separated by blank lines
  html = html.replace(/\n\n+/g, "\n</p><p>\n");
  html = `<p>${html}</p>`;
  html = html.replace(/<p>\s*<(h[1-4]|table|ul|ol|pre|blockquote)/g, "<$1");
  html = html.replace(/<\/(h[1-4]|table|ul|ol|pre|blockquote)>\s*<\/p>/g, "</$1>");
  html = html.replace(/<p>\s*<\/p>/g, "");

  // Line breaks within paragraphs
  html = html.replace(/\n/g, "<br/>");

  return html;
}
