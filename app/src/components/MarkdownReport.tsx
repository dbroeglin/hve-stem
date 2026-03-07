import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "github-markdown-css/github-markdown.css";

interface MarkdownReportProps {
  content: string;
}

/** Render a Markdown assessment report as styled HTML. */
export function MarkdownReport({
  content,
}: MarkdownReportProps): React.ReactElement {
  return (
    <div className="markdown-body">
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  );
}
