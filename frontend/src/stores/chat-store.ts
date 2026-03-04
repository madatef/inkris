import { create } from 'zustand';
import apiClient from '@/lib/api-client';
import type {
  ConversationResponse,
  ConversationCreate,
  ConversationUpdate,
  MessageResponse,
  ChatMessageCreate,
  ConversationMessages,
  ConversationMessagesResponse,
  UserConversationsRequest,
  UserConversationsResponse,
} from '@/types/api';

interface ChatState {
  conversations: ConversationResponse[];
  activeConversationId: string | null;
  messages: Map<string, MessageResponse[]>;
  messageCursors: Map<string, string | null>;
  hasNextMessages: Map<string, boolean>;
  isStreaming: boolean;
  streamingMessage: string;
  ephemeralMessage: string | null;
  isLoading: boolean;
  isFetchingMessages: boolean;
  error: string | null;
  totalConversations: number;

  // Actions
  fetchConversations: (page: number, pageSize: number) => Promise<void>;
  createConversation: (data: ConversationCreate) => Promise<ConversationResponse>;
  setActiveConversation: (id: string | null) => void;
  fetchMessages: (conversationId: string, limit: number, cursor?: string) => Promise<void>;
  sendMessage: (conversationId: string, content: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  renameConversation: (id: string, title: string) => Promise<void>;
  addMessage: (message: MessageResponse) => void;
  appendStreamingToken: (token: string) => void;
  setEphemeralMessage: (message: string | null) => void;
  finalizeStreamingMessage: (conversationId: string) => void;
  resetStreaming: () => void;
  clearError: () => void;
  getConversationById: (id: string) => ConversationResponse | undefined;
}

async function fetchWithRefresh(
  input: RequestInfo,
  init: RequestInit,
  refresh: () => Promise<void>,
  retry = true
): Promise<Response> {
  const response = await fetch(input, {
    ...init,
    credentials: 'include',
  });

  if (response.status === 401) {
    if (retry) {
      await refresh();
      return fetchWithRefresh(input, init, refresh, false);
    } else {
      window.alert("Session Expired. Please relogin");
      window.location.href = '/login'
    }
  }

  return response;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: new Map(),
  messageCursors: new Map(),
  hasNextMessages: new Map(),
  isStreaming: false,
  streamingMessage: '',
  ephemeralMessage: null,
  isLoading: false,
  isFetchingMessages: false,
  error: null,
  totalConversations: 0,

  fetchConversations: async (page: number, pageSize: number) => {
    set({ isLoading: true, error: null });
    try {
      const request: UserConversationsRequest = { page, page_size: pageSize };
      const response = await apiClient.post<UserConversationsResponse>(
        '/chat/conversations/all',
        request
      );
      set({ 
        conversations: response.items, 
        totalConversations: response.total,
        isLoading: false 
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch conversations';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  createConversation: async (data: ConversationCreate) => {
    set({ error: null });
    try {
      const conversation = await apiClient.post<ConversationResponse>(
        '/chat/conversations/create',
        data
      );
      set((state) => ({
        conversations: [conversation, ...state.conversations],
        totalConversations: state.totalConversations + 1,
      }));
      return conversation;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create conversation';
      set({ error: errorMessage });
      throw error;
    }
  },

  setActiveConversation: (id: string | null) => {
    set({ activeConversationId: id });
  },

  fetchMessages: async (conversationId: string, limit: number, cursor?: string) => {
    set({ isFetchingMessages: true, error: null });
    try {
      const request: ConversationMessages = {
        limit,
        cursor: cursor || undefined,
      };
      const response = await apiClient.post<ConversationMessagesResponse>(
        `/chat/conversations/${conversationId}/list-messages`,
        request
      );

      set((state) => {
        const existingMessages = state.messages.get(conversationId) || [];
        
        // When loading more (with cursor), prepend to existing messages
        // Otherwise, replace with new messages
        const resMessages = response.items.reverse();
        let newMessages;

        if (cursor) {
          const existingIds = new Set(existingMessages.map(m => m.id));
          const uniqueMessages = resMessages.filter(m => !existingIds.has(m.id));
          newMessages = [...uniqueMessages, ...existingMessages];
        } else {
          newMessages = resMessages;
        }

        const updatedMessages = new Map(state.messages);
        updatedMessages.set(conversationId, newMessages);

        const updatedCursors = new Map(state.messageCursors);
        updatedCursors.set(conversationId, response.next_cursor);

        const updatedHasNext = new Map(state.hasNextMessages);
        updatedHasNext.set(conversationId, response.has_next);

        return {
          messages: updatedMessages,
          messageCursors: updatedCursors,
          hasNextMessages: updatedHasNext,
          isFetchingMessages: false,
        };
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch messages';
      set({ error: errorMessage, isFetchingMessages: false });
      throw error;
    }
  },

  sendMessage: async (conversationId: string, content: string) => {
    const userMessage: MessageResponse = {
      id: crypto.randomUUID(),
      conversation_id: conversationId,
      role: 'user',
      content,
    };

    // Add user message immediately
    get().addMessage(userMessage);

    // Start streaming
    set({ 
      isStreaming: true, 
      streamingMessage: '', 
      ephemeralMessage: null,
      error: null 
    });

    try {
      const messageData: ChatMessageCreate = { content };
      const response = await fetchWithRefresh(
        `/api/v0/chat/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(messageData),
        },
        () => apiClient.refreshToken()
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const data = line.slice(5).trim();
            
            if (!data) continue;

            try {
              const parsed = JSON.parse(data);

              if (currentEvent === 'token' && parsed.message) {
                // Append token to streaming message
                get().appendStreamingToken(parsed.message);
                get().setEphemeralMessage(null);
              } else if (currentEvent === 'status' && parsed.message) {
                // Show ephemeral status message
                get().setEphemeralMessage(parsed.message);
              } else if (currentEvent === 'tool' && parsed.message) {
                // Show ephemeral tool message
                get().setEphemeralMessage(parsed.message);
              } else if (currentEvent === 'error' && parsed.message) {
                // Handle error
                throw new Error(parsed.message);
              } else if (currentEvent === 'done' && parsed.ok) {
                // Finalize the message
                get().finalizeStreamingMessage(conversationId);
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError);
            }
          }
        }
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to send message';
      set({ 
        error: errorMessage, 
        isStreaming: false,
        streamingMessage: '',
        ephemeralMessage: null,
      });
      throw error;
    }
  },

  deleteConversation: async (id: string) => {
    set({ error: null });
    try {
      await apiClient.delete(`/chat/conversations/${id}`);
      set((state) => {
        // Remove conversation
        const updatedConversations = state.conversations.filter((c) => c.id !== id);
        
        // Remove messages for this conversation
        const updatedMessages = new Map(state.messages);
        updatedMessages.delete(id);
        
        // Remove cursors
        const updatedCursors = new Map(state.messageCursors);
        updatedCursors.delete(id);
        
        // Remove hasNext
        const updatedHasNext = new Map(state.hasNextMessages);
        updatedHasNext.delete(id);
        
        return {
          conversations: updatedConversations,
          messages: updatedMessages,
          messageCursors: updatedCursors,
          hasNextMessages: updatedHasNext,
          activeConversationId: state.activeConversationId === id ? null : state.activeConversationId,
          totalConversations: Math.max(0, state.totalConversations - 1),
        };
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to delete conversation';
      set({ error: errorMessage });
      throw error;
    }
  },

  renameConversation: async (id: string, title: string) => {
    set({ error: null });
    try {
      const data: ConversationUpdate = { title };
      const updated = await apiClient.patch<ConversationResponse>(
        `/chat/conversations/${id}/rename`,
        data
      );
      set((state) => ({
        conversations: state.conversations.map((c) => (c.id === id ? updated : c)),
      }));
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to rename conversation';
      set({ error: errorMessage });
      throw error;
    }
  },

  addMessage: (message: MessageResponse) => {
    set((state) => {
      const conversationMessages = state.messages.get(message.conversation_id) || [];
      const updatedMessages = new Map(state.messages);
      updatedMessages.set(message.conversation_id, [...conversationMessages, message]);
      return { messages: updatedMessages };
    });
  },

  appendStreamingToken: (token: string) => {
    set((state) => ({
      streamingMessage: state.streamingMessage + token,
    }));
  },

  setEphemeralMessage: (message: string | null) => {
    set({ ephemeralMessage: message });
  },

  finalizeStreamingMessage: (conversationId: string) => {
    const { streamingMessage } = get();
    
    if (streamingMessage.trim()) {
      const assistantMessage: MessageResponse = {
        id: crypto.randomUUID(),
        conversation_id: conversationId,
        role: 'assistant',
        content: streamingMessage,
      };
      get().addMessage(assistantMessage);
    }

    set({
      isStreaming: false,
      streamingMessage: '',
      ephemeralMessage: null,
    });
  },

  resetStreaming: () => {
    set({
      isStreaming: false,
      streamingMessage: '',
      ephemeralMessage: null,
    });
  },

  clearError: () => set({ error: null }),

  getConversationById: (id: string) => {
    return get().conversations.find((c) => c.id === id);
  },
}));