import { useEffect, useRef } from 'react';
import { useChatStore } from '@/stores/chat-store';
import MessageBubble from './MessageBubble';
import AssistantMessage from './AssistantMessage';
import { Loader2 } from 'lucide-react';

interface MessageListProps {
  conversationId: string;
}

export default function MessageList({ conversationId }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef(0);
  const prevScrollHeightRef = useRef(0);
  const lastMessageIdRef = useRef<string | null>(null);
  const lastMessageRoleRef = useRef<string | null>(null);

  const {
    messages,
    messageCursors,
    hasNextMessages,
    fetchMessages,
    isFetchingMessages,
    isStreaming,
    streamingMessage,
    ephemeralMessage,
  } = useChatStore();

  const conversationMessages = messages.get(conversationId) || [];
  const cursor = messageCursors.get(conversationId);
  const hasNext = hasNextMessages.get(conversationId);

  // Check if user is at bottom of scroll
  const isAtBottom = () => {
    if (!scrollRef.current) return false;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    return scrollHeight - scrollTop - clientHeight < 10;
  };

  // Scroll to bottom helper
  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  // Handle scroll position preservation when loading older messages
  useEffect(() => {
    const prevCount = prevMessageCountRef.current;
    const currentCount = conversationMessages.length;
    const lastMessage = conversationMessages[conversationMessages.length - 1];
    const lastMessageId = lastMessage?.id;
    const lastMessageRole = lastMessage?.role;
    
    // Initial load - scroll to bottom
    if (prevCount === 0 && currentCount > 0) {
      scrollToBottom();
    }
    // Loading older messages (prepending) - detect by checking if last message ID is the same
    else if (currentCount > prevCount && lastMessageIdRef.current === lastMessageId) {
      if (scrollRef.current) {
        const newScrollHeight = scrollRef.current.scrollHeight;
        const heightDifference = newScrollHeight - prevScrollHeightRef.current;
        scrollRef.current.scrollTop += heightDifference;
      }
    }
    // New message appended (last message ID changed) - always scroll to bottom
    else if (currentCount > prevCount && lastMessageIdRef.current !== lastMessageId) {
      scrollToBottom();
    }
    
    prevMessageCountRef.current = currentCount;
    prevScrollHeightRef.current = scrollRef.current?.scrollHeight || 0;
    lastMessageIdRef.current = lastMessageId || null;
    lastMessageRoleRef.current = lastMessageRole || null;
  }, [conversationMessages.length, conversationMessages[-1]?.id]);

  // Handle streaming and ephemeral messages - only if already at bottom
  useEffect(() => {
    if ((streamingMessage || ephemeralMessage) && isAtBottom()) {
      scrollToBottom();
    }
  }, [streamingMessage, ephemeralMessage]);

  const handleScroll = () => {
    if (!scrollRef.current) return;

    const { scrollTop, scrollHeight } = scrollRef.current;
    const isAtTop = scrollTop <= 10;

    // Load more messages when scrolled to top
    if (isAtTop && hasNext && !isFetchingMessages && cursor) {
      prevScrollHeightRef.current = scrollHeight;
      fetchMessages(conversationId, 10, cursor);
    }
  };


  return (
    <div
      ref={scrollRef}
      onScroll={handleScroll}
      className="h-full overflow-y-auto space-y-6 scroll-smooth"
    >
      {/* Loading indicator for pagination */}
      {isFetchingMessages && hasNext && (
        <div className="flex justify-center py-4">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Messages */}
      {conversationMessages.map((message) => {
        if (message.role === 'user') {
          return <MessageBubble key={message.id} content={message.content} />;
        } else {
          return <AssistantMessage key={message.id} content={message.content} />;
        }
      })}

      {/* Streaming Message */}
      {isStreaming && (
        <div className="space-y-2">
          {ephemeralMessage && (
            <div className="text-sm text-muted-foreground animate-pulse-soft">
              {ephemeralMessage}
            </div>
          )}
          {streamingMessage && <AssistantMessage content={streamingMessage} isStreaming />}
        </div>
      )}

      {/* Empty state */}
      {conversationMessages.length === 0 && !isStreaming && !isFetchingMessages && (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <p className="text-muted-foreground">No messages yet. Ready to send your first message?</p>
        </div>
      )}
      {conversationMessages.length === 0 && isFetchingMessages && (
        <div className="flex justify-center py-4 h-full">
          <Loader2 className="h-8 w-8 my-auto animate-spin text-muted-foreground" />
        </div>
      )

      }
    </div>
  );
}