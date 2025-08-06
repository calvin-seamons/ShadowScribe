import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import 'highlight.js/styles/github-dark.css';

interface EnhancedMarkdownProps {
  content: string;
  className?: string;
}

const EnhancedMarkdown: React.FC<EnhancedMarkdownProps> = ({ content, className = '' }) => {
  return (
    <div className={`enhanced-markdown ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={{
          // Enhanced headings
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold text-purple-300 mb-4 pb-2 border-b border-gray-700">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-semibold text-purple-300 mb-3 mt-6">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-lg font-semibold text-blue-300 mb-2 mt-4">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-base font-semibold text-blue-300 mb-2 mt-3">
              {children}
            </h4>
          ),
          h5: ({ children }) => (
            <h5 className="text-sm font-semibold text-blue-300 mb-1 mt-2">
              {children}
            </h5>
          ),
          h6: ({ children }) => (
            <h6 className="text-sm font-semibold text-blue-300 mb-1 mt-2">
              {children}
            </h6>
          ),
          
          // Enhanced paragraphs with proper spacing
          p: ({ children }) => (
            <p className="mb-4 leading-relaxed text-gray-100 last:mb-0">
              {children}
            </p>
          ),
          
          // Enhanced lists
          ul: ({ children }) => (
            <ul className="mb-4 pl-6 space-y-1">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 pl-6 space-y-1 list-decimal">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-100 leading-relaxed">
              {children}
            </li>
          ),
          
          // Enhanced tables
          table: ({ children }) => (
            <div className="mb-6 overflow-x-auto">
              <table className="min-w-full border border-gray-600 rounded-lg overflow-hidden">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-700">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-gray-600">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-gray-750 transition-colors">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-4 py-3 text-left text-sm font-semibold text-purple-300 border-b border-gray-600">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-3 text-sm text-gray-100 border-b border-gray-700">
              {children}
            </td>
          ),
          
          // Enhanced code blocks
          pre: ({ children }) => (
            <pre className="mb-4 p-4 bg-gray-800 rounded-lg border border-gray-700 overflow-x-auto">
              {children}
            </pre>
          ),
          code: ({ className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');
            const isInline = !match;
            
            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 bg-gray-700 text-purple-300 rounded text-sm font-mono" {...props}>
                  {children}
                </code>
              );
            }
            
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          
          // Enhanced blockquotes
          blockquote: ({ children }) => (
            <blockquote className="mb-4 pl-4 border-l-4 border-purple-500 bg-gray-800 p-4 rounded-r-lg italic">
              {children}
            </blockquote>
          ),
          
          // Enhanced links
          a: ({ href, children }) => (
            <a 
              href={href} 
              className="text-blue-400 hover:text-blue-300 underline transition-colors"
              target="_blank" 
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          
          // Enhanced horizontal rules
          hr: () => (
            <hr className="my-6 border-gray-600" />
          ),
          
          // Enhanced emphasis
          strong: ({ children }) => (
            <strong className="font-semibold text-purple-300">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-blue-300">
              {children}
            </em>
          ),
          
          // Enhanced strikethrough (from remarkGfm)
          del: ({ children }) => (
            <del className="line-through text-gray-400">
              {children}
            </del>
          ),
          
          // Task lists (from remarkGfm)
          input: ({ type, checked, ...props }) => {
            if (type === 'checkbox') {
              return (
                <input
                  type="checkbox"
                  checked={checked}
                  readOnly
                  className="mr-2 accent-purple-500"
                  {...props}
                />
              );
            }
            return <input type={type} {...props} />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default EnhancedMarkdown;
