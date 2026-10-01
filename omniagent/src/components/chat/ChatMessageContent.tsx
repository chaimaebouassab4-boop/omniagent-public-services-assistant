import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileText, Sparkles, AlertCircle } from "lucide-react";

interface ChatMessageContentProps {
  content: string;
  role: "user" | "assistant";
  isRtl?: boolean;
}

const DOCUMENT_PREFIX = "[Document] ";

export const ChatMessageContent: React.FC<ChatMessageContentProps> = ({
  content,
  role,
  isRtl = false,
}) => {
  // Handle user uploaded document attachment label
  if (content.startsWith(DOCUMENT_PREFIX)) {
    const rest = content.slice(DOCUMENT_PREFIX.length);
    const newlineIndex = rest.indexOf("\n\n");
    const filename = newlineIndex !== -1 ? rest.slice(0, newlineIndex).trim() : rest.trim();
    const accompanyingText = newlineIndex !== -1 ? rest.slice(newlineIndex + 2).trim() : "";

    return (
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2.5 px-3 py-2 rounded-xl bg-card/15 border border-white/20 text-white font-medium text-xs sm:text-sm shadow-xs">
          <div className="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center shrink-0">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="truncate max-w-[200px] sm:max-w-[300px] font-semibold">{filename}</span>
            <span className="text-[10px] text-white/80">Document joint</span>
          </div>
        </div>
        {accompanyingText && (
          <div className="whitespace-pre-wrap break-words">{accompanyingText}</div>
        )}
      </div>
    );
  }

  // User simple messages: preserve line breaks, render plain text cleanly
  if (role === "user") {
    return <div className="whitespace-pre-wrap break-words">{content}</div>;
  }

  // Assistant messages: render Rich Markdown with custom components
  return (
    <div
      className={`chat-markdown-content break-words text-sm leading-7 ${
        isRtl ? "text-right" : "text-left"
      }`}
      dir={isRtl ? "rtl" : "ltr"}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-3 mt-4 flex items-center gap-2 border-b border-border/60 pb-2 text-base font-bold text-foreground">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-2 mt-4 flex items-center gap-1.5 text-sm font-bold text-foreground">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-2 mt-4 flex items-center gap-1.5 border-b border-border/40 pb-1 text-sm font-semibold text-[#17365d] dark:text-foreground">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="mb-1.5 mt-3 text-sm font-semibold text-foreground">{children}</h4>
          ),
          p: ({ children }) => (
            <p className="my-2 leading-7 text-card-foreground">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="my-3 list-disc space-y-2 ps-5 marker:text-primary">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-3 list-decimal space-y-2 ps-5 marker:font-semibold marker:text-primary">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="ps-1 leading-7 text-card-foreground">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          em: ({ children }) => {
            const text = String(children);
            // Check if this is the OCR badge italic text
            if (
              text.includes("OCR") ||
              text.includes("Reconnaissance optique") ||
              text.includes("التعرف الضوئي")
            ) {
              return (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 my-1 rounded-full text-[11px] font-medium bg-primary/10 text-primary border border-primary/20">
                  <Sparkles className="w-3 h-3 shrink-0" />
                  <span>{children}</span>
                </span>
              );
            }
            return <em className="italic text-muted-foreground">{children}</em>;
          },
          hr: () => <hr className="my-3 border-t border-border/60" />,
          blockquote: ({ children }) => (
            <blockquote className="border-s-4 border-primary/50 bg-primary/5 px-3 py-2 my-2.5 rounded-e text-xs text-foreground/90 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div className="flex-1">{children}</div>
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2 rounded-lg border border-border">
              <table className="min-w-full divide-y divide-border text-xs">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 bg-muted font-semibold text-foreground text-start">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-1.5 border-t border-border text-muted-foreground">
              {children}
            </td>
          ),
          code: ({ children }) => (
            <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-[11px] text-foreground">
              {children}
            </code>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
