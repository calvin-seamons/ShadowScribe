import React from 'react';
import clsx from 'clsx';

interface StatBlockProps {
  title: string;
  stats: Record<string, string | number>;
  className?: string;
}

export const StatBlock: React.FC<StatBlockProps> = ({ title, stats, className = '' }) => {
  return (
    <div className={clsx('bg-gray-800 border border-gray-600 rounded-lg p-4 mb-4', className)}>
      <h3 className="text-lg font-semibold text-purple-300 mb-3 border-b border-gray-600 pb-2">
        {title}
      </h3>
      <div className="space-y-2">
        {Object.entries(stats).map(([key, value]) => (
          <div key={key} className="flex justify-between items-center">
            <span className="text-gray-300 font-medium">{key}:</span>
            <span className="text-blue-300 font-mono">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

interface FormattedTableProps {
  headers: string[];
  rows: (string | number)[][];
  className?: string;
}

export const FormattedTable: React.FC<FormattedTableProps> = ({ headers, rows, className = '' }) => {
  return (
    <div className={clsx('overflow-x-auto mb-6', className)}>
      <table className="min-w-full border border-gray-600 rounded-lg overflow-hidden">
        <thead className="bg-gray-700">
          <tr>
            {headers.map((header, index) => (
              <th
                key={index}
                className="px-4 py-3 text-left text-sm font-semibold text-purple-300 border-b border-gray-600"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-600">
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-gray-750 transition-colors">
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className="px-4 py-3 text-sm text-gray-100 border-b border-gray-700"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  className?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ 
  code, 
  language = 'text', 
  title, 
  className = '' 
}) => {
  return (
    <div className={clsx('mb-4', className)}>
      {title && (
        <div className="bg-gray-700 px-4 py-2 text-sm font-medium text-purple-300 rounded-t-lg border border-gray-600 border-b-0">
          <span>{title}</span>
          {language !== 'text' && (
            <span className="ml-2 text-xs text-gray-400">({language})</span>
          )}
        </div>
      )}
      <pre className={clsx(
        'p-4 bg-gray-800 border border-gray-700 overflow-x-auto',
        title ? 'rounded-b-lg' : 'rounded-lg'
      )}>
        <code className="text-sm text-gray-100 font-mono leading-relaxed">
          {code}
        </code>
      </pre>
    </div>
  );
};
