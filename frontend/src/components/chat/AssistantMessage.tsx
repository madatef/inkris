import React from 'react'
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Download } from 'lucide-react';
import { Button } from '../ui/button';

interface AssistantMessageProps {
  content: string;
  isStreaming?: boolean;
}

export default function AssistantMessage({ content, isStreaming = false }: AssistantMessageProps) {
  return (
    <div className="max-w-full">
      <div className="markdown-content max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            // Custom link renderer to handle video
            a: ({ node, className, ref, children, href, ...props }) => {
              // Check if this is a video link: [video](url)
              const childrenArray = React.Children.toArray(children);
              const isVideo = childrenArray?.[0] === 'video';
              
              if (isVideo && href) {
                return (
                  <div className="relative my-4 group">
                    <video
                      src={href}
                      controls
                      className="w-full rounded-lg"
                    />
                    <Button
                      size="icon"
                      variant="secondary"
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => window.open(href, '_blank')}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                );
              }

              return (
                <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                  {children}
                </a>
              );
            },
            // Custom image renderer with download button
            img: ({ src, alt, ...props }) => {
              return (
                <div className="relative my-4 group">
                  <img
                    src={src}
                    alt={alt}
                    className="rounded-lg"
                    {...props}
                  />
                  <Button
                    size="icon"
                    variant="secondary"
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => window.open(src, '_blank')}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              );
            },
            // Code blocks
            code: ({ node, className, children, ...props }) => {
              const match = /language-(\w+)/.exec(className || '');
              const language = match?.[1];
            
              if (!language) {
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              }
            
              return (
                <div className="m-0 p-0 overflow-x-auto rounded-lg">
                  <SyntaxHighlighter
                    language={language}
                    PreTag="div"
                    style={vscDarkPlus}
                    customStyle={{
                      background: 'transparent',
                      margin: 0,
                    }}
                    codeTagProps={{
                      style: {
                        background: 'transparent',
                      },
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                </div>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
        {isStreaming && <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1" />}
      </div>
    </div>
  );
}