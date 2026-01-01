import { useState, useRef, useEffect } from 'react';

interface Props {
  onSend: (message: string) => void;
  onCancel: () => void;
  disabled: boolean;
  isLoading: boolean;
}

export function ChatInput({ onSend, onCancel, disabled, isLoading }: Props) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-end">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-echo-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
      />
      {isLoading ? (
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          Cancel
        </button>
      ) : (
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-4 py-2 bg-echo-500 text-white rounded-lg hover:bg-echo-600 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Send
        </button>
      )}
    </form>
  );
}
