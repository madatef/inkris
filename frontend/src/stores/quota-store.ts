import { create } from 'zustand';
import apiClient from '@/lib/api-client';
import type { UserQuota } from '@/types/api';

interface QuotaState {
  quotas: UserQuota | null;
  isLoading: boolean;
  error: string | null;
  lastFetchTime: number | null;

  // Actions
  fetchQuotas: (force?: boolean) => Promise<void>;
  canUploadFile: (sizeBytes: number) => boolean;
  canSendMessage: () => boolean;
  canCreateConversation: () => boolean;
  getWarnings: () => string[];
  isQuotaExhausted: (quotaType: keyof UserQuota) => boolean;
  clearError: () => void;
}

const QUOTA_THRESHOLDS = {
  tokens: 5000,
  storage: 20_000_000, // 20 MB
  other: 1,
};

// Cache duration: 30 seconds
const CACHE_DURATION = 30 * 1000;

export const useQuotaStore = create<QuotaState>((set, get) => ({
  quotas: null,
  isLoading: false,
  error: null,
  lastFetchTime: null,

  fetchQuotas: async (force = false) => {
    const state = get();
    const now = Date.now();

    // Use cache if available and not forcing refresh
    if (!force && state.lastFetchTime && (now - state.lastFetchTime) < CACHE_DURATION) {
      return;
    }

    set({ isLoading: true, error: null });
    try {
      const quotas = await apiClient.get<UserQuota>('/usage/status');
      set({ 
        quotas, 
        isLoading: false,
        lastFetchTime: now,
        error: null 
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch quotas';
      set({ 
        error: errorMessage, 
        isLoading: false 
      });
      throw error;
    }
  },

  canUploadFile: (sizeBytes: number) => {
    const { quotas } = get();
    if (!quotas) return false;
    
    return (
      quotas.files > 0 && 
      quotas.file_processing > 0 && 
      quotas.storage_bytes >= sizeBytes
    );
  },

  canSendMessage: () => {
    const { quotas } = get();
    if (!quotas) return false;
    return quotas.llm_tokens > 0;
  },

  canCreateConversation: () => {
    const { quotas } = get();
    if (!quotas) return false;
    return quotas.conversations > 0;
  },

  getWarnings: () => {
    const { quotas } = get();
    if (!quotas) return [];

    const warnings: string[] = [];

    if (quotas.llm_tokens <= QUOTA_THRESHOLDS.tokens && quotas.llm_tokens > 0) {
      warnings.push(`Only ${quotas.llm_tokens.toLocaleString()} tokens remaining`);
    }

    if (quotas.storage_bytes <= QUOTA_THRESHOLDS.storage && quotas.storage_bytes > 0) {
      const mb = Math.round(quotas.storage_bytes / 1_000_000);
      warnings.push(`Only ${mb}MB storage remaining`);
    }

    if (quotas.files <= QUOTA_THRESHOLDS.other && quotas.files > 0) {
      warnings.push(`Only ${quotas.files} file slot${quotas.files > 1 ? 's' : ''} remaining`);
    }

    if (quotas.conversations <= QUOTA_THRESHOLDS.other && quotas.conversations > 0) {
      warnings.push(`Only ${quotas.conversations} conversation${quotas.conversations > 1 ? 's' : ''} remaining`);
    }

    if (quotas.web_searches <= QUOTA_THRESHOLDS.other && quotas.web_searches > 0) {
      warnings.push(`Only ${quotas.web_searches} web search${quotas.web_searches > 1 ? 'es' : ''} remaining`);
    }

    if (quotas.image_generations <= QUOTA_THRESHOLDS.other && quotas.image_generations > 0) {
      warnings.push(`Only ${quotas.image_generations} image generation${quotas.image_generations > 1 ? 's' : ''} remaining`);
    }

    if (quotas.video_generations <= QUOTA_THRESHOLDS.other && quotas.video_generations > 0) {
      warnings.push(`Only ${quotas.video_generations} video generation${quotas.video_generations > 1 ? 's' : ''} remaining`);
    }

    return warnings;
  },

  isQuotaExhausted: (quotaType: keyof UserQuota) => {
    const { quotas } = get();
    if (!quotas) return true;
    return quotas[quotaType] <= 0;
  },

  clearError: () => set({ error: null }),
}));