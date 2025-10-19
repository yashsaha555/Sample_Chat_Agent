"use client";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

export default function Markdown({ content }: { content: string }) {
  return (
    <div className="prose prose-invert max-w-none prose-headings:mt-2 prose-headings:mb-1 prose-p:my-1 prose-ol:my-2 prose-ul:my-2 prose-li:my-0 prose-pre:my-2">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          p: ({ node, ...props }) => <p className="my-1" {...props} />,
          li: ({ node, ...props }) => <li className="my-0" {...props} />,
          ul: ({ node, ...props }) => <ul className="my-2 pl-5" {...props} />,
          ol: ({ node, ...props }) => <ol className="my-2 pl-5" {...props} />,
          h1: ({ node, ...props }) => <h1 className="mt-2 mb-1" {...props} />,
          h2: ({ node, ...props }) => <h2 className="mt-2 mb-1" {...props} />,
          h3: ({ node, ...props }) => <h3 className="mt-2 mb-1" {...props} />,
          h4: ({ node, ...props }) => <h4 className="mt-2 mb-1" {...props} />,
          pre: ({ node, ...props }) => <pre className="my-2" {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
