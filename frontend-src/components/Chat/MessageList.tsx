import { User, Bot } from 'lucide-react';
import clsx from 'clsx';
import type { Message } from '../../types/index';
import EnhancedMarkdown from '../Common/EnhancedMarkdown';
import SourceUsageDisplay from './SourceUsageDisplay';
import { SourceUsageErrorBoundary } from './SourceUsageErrorBoundary';

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="flex flex-col space-y-6 p-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={clsx(
            'flex items-start space-x-4',
            message.type === 'user' ? 'justify-end' : 'justify-start'
          )}
        >
          {message.type === 'assistant' && (
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center shadow-lg">
              <Bot className="w-6 h-6 text-white" />
            </div>
          )}
          
          <div
            className={clsx(
              'max-w-4xl',
              message.type === 'user' ? 'flex-col' : 'flex-col'
            )}
          >
            <div
              className={clsx(
                'px-6 py-4 rounded-xl shadow-lg',
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100 border border-gray-700'
              )}
            >
              {message.type === 'user' ? (
                <p className="leading-relaxed">{message.content}</p>
              ) : (
                <EnhancedMarkdown 
                  content={message.content} 
                  className="max-w-none"
                />
              )}
              <p className="text-xs opacity-60 mt-3 text-right">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
            
            {/* Show source usage for assistant messages */}
            {message.type === 'assistant' && message.sourceUsage && (
              <SourceUsageErrorBoundary>
                <SourceUsageDisplay sourceUsage={message.sourceUsage} />
              </SourceUsageErrorBoundary>
            )}
          </div>

          {message.type === 'user' && (
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center shadow-lg">
              <User className="w-6 h-6 text-white" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
