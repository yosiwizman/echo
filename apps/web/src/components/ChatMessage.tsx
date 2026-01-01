import { useState } from 'react';
import type { ChatMessage as ChatMessageType, ResponseMetadata } from '../types';

interface Props {
  message: ChatMessageType;
}

function MetadataPanel({ metadata }: { metadata: ResponseMetadata }) {
  return (
    <div className="mt-2 p-2 bg-gray-100 rounded text-xs text-gray-600 font-mono">
      <div className="font-semibold text-gray-700 mb-1">Debug Info</div>
      <div className="grid grid-cols-2 gap-1">
        {metadata.trace_id && (
          <>
            <span className="text-gray-500">trace_id:</span>
            <span className="truncate">{metadata.trace_id}</span>
          </>
        )}
        {metadata.provider && (
          <>
            <span className="text-gray-500">provider:</span>
            <span>{metadata.provider}</span>
          </>
        )}
        {metadata.env && (
          <>
            <span className="text-gray-500">env:</span>
            <span>{metadata.env}</span>
          </>
        )}
        {metadata.git_sha && (
          <>
            <span className="text-gray-500">git_sha:</span>
            <span className="truncate">{metadata.git_sha.slice(0, 7)}</span>
          </>
        )}
        {metadata.build_time && (
          <>
            <span className="text-gray-500">build_time:</span>
            <span className="truncate">{metadata.build_time}</span>
          </>
        )}
        {metadata.model && (
          <>
            <span className="text-gray-500">model:</span>
            <span>{metadata.model}</span>
          </>
        )}
        {metadata.tokens_used !== undefined && (
          <>
            <span className="text-gray-500">tokens:</span>
            <span>{metadata.tokens_used}</span>
          </>
        )}
      </div>
    </div>
  );
}

export function ChatMessage({ message }: Props) {
  const [showMetadata, setShowMetadata] = useState(false);
  const isUser = message.role === 'user';
  const hasMetadata = message.metadata && Object.keys(message.metadata).length > 0;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser ? 'bg-echo-500 text-white' : 'bg-gray-200 text-gray-900'
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{message.content || '...'}</div>

        {hasMetadata && (
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className={`mt-1 text-xs underline ${
              isUser ? 'text-echo-100 hover:text-white' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {showMetadata ? 'Hide debug' : 'Show debug'}
          </button>
        )}

        {showMetadata && message.metadata && <MetadataPanel metadata={message.metadata} />}

        <div
          className={`text-xs mt-1 ${isUser ? 'text-echo-200' : 'text-gray-400'}`}
        >
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
