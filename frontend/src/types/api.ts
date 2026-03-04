// API Types based on OpenAPI spec

export interface UserCreate {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }
  
  export interface UserLogin {
    email: string;
    password: string;
  }
  
  export interface UserResponse {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    created_at: string;
    updated_at: string;
  }
  
  export interface UserQuota {
    files: number;
    file_processing: number;
    storage_bytes: number;
    conversations: number;
    web_searches: number;
    web_scraping: number;
    image_generations: number;
    video_generations: number;
    llm_tokens: number;
  }
  
  export type FileExtension = 'pdf' | 'txt' | 'md' | 'xls' | 'xlsx';
  export type FileStatus = 'pending' | 'uploaded' | 'processing' | 'ready' | 'error' | 'deleted';
  
  export interface FilePresigned {
    name: string;
    extension: FileExtension;
    description?: string;
    size_bytes: number;
  }
  
  export interface FileResponse {
    id: string;
    name: string;
    extension: FileExtension;
    size_bytes: number;
    description: string | null;
    status: FileStatus;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;
  }
  
  export interface FileUpdate {
    name?: string;
    description?: string;
  }
  
  export interface UploadSpec {
    method: string;
    url: string;
    headers: Record<string, string> | null;
    fields: Record<string, string> | null;
    expires_at: string;
  }
  
  export interface PresignedResponse {
    file_id: string;
    upload: UploadSpec;
  }
  
  export interface FileComplete {
    success: boolean;
  }
  
  export interface CompleteResponse {
    success: boolean;
    message: string;
  }
  
  export type ConversationScope = 'file' | 'studio';
  
  export interface ConversationCreate {
    scope?: ConversationScope;
    file_id?: string;
    title?: string;
  }
  
  export interface ConversationResponse {
    id: string;
    scope: string;
    file_id: string | null;
    title: string | null;
    created_at: string;
    updated_at: string;
  }
  
  export interface ConversationUpdate {
    title: string;
  }
  
  export type MessageRole = 'user' | 'assistant';
  
  export interface MessageResponse {
    id: string;
    conversation_id: string;
    role: MessageRole;
    content: string;
  }
  
  export interface ChatMessageCreate {
    content: string;
  }
  
  export interface ConversationMessages {
    limit: number;
    cursor?: string;
  }
  
  export interface ConversationMessagesResponse {
    items: MessageResponse[];
    next_cursor: string | null;
    has_next: boolean;
  }
  
  export interface UserConversationsRequest {
    page: number;
    page_size: number;
  }
  
  export interface UserConversationsResponse {
    page: number;
    page_size: number;
    total: number;
    has_next: boolean;
    items: ConversationResponse[];
  }
  
  export interface AppError {
    code: string;
    status_code: number;
    message: string;
    field?: string;
  }
  
  export interface ValidationError {
    detail: Array<{
      loc: (string | number)[];
      msg: string;
      type: string;
    }>;
  }
  
  // SSE Event Types
  export type AgentEventType = 'status' | 'tool' | 'token' | 'error' | 'done';
  
  export interface AgentEvent {
    event: AgentEventType;
    data: {
      message?: string;
      ok?: boolean;
    };
  }
  
  export interface FileProcessingEvent {
    file_id: string;
    user_id: string;
    status: 'processing' | 'ready' | 'error';
    progress: number;
    error?: string;
  }