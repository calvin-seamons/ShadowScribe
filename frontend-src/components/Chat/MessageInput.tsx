import { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-700 p-4">
      <div className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={disabled}
          placeholder={disabled ? "Processing..." : "Ask about D&D rules, your character, or past sessions..."}
          className="flex-1 bg-gray-800 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      
      {/* Quick Actions */}
      <div className="mt-2 flex flex-wrap gap-2">
        {['What\'s my AC?', 'Show my spells', 'Last session summary'].map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSendMessage(suggestion)}
            disabled={disabled}
            className="text-xs bg-gray-800 text-gray-400 px-3 py-1 rounded-full hover:bg-gray-700 hover:text-white transition-colors disabled:opacity-50"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};
