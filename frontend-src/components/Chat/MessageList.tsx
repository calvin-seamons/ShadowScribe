import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';
import clsx from 'clsx';
import type { Message } from '../../types/index';

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="flex flex-col space-y-4 p-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={clsx(
            'flex items-start space-x-3',
            message.type === 'user' ? 'justify-end' : 'justify-start'
          )}
        >
          {message.type === 'assistant' && (
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
          )}
          
          <div
            className={clsx(
              'max-w-2xl px-4 py-2 rounded-lg',
              message.type === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-100'
            )}
          >
            {message.type === 'user' ? (
              <p>{message.content}</p>
            ) : (
              <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                {message.content}
              </ReactMarkdown>
            )}
            <p className="text-xs opacity-50 mt-1">
              {message.timestamp.toLocaleTimeString()}
            </p>
          </div>

          {message.type === 'user' && (
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
