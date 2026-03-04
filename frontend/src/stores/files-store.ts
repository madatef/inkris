import { create } from 'zustand';
import apiClient from '@/lib/api-client';
import axios from 'axios';
import type {
  FileResponse,
  FilePresigned,
  PresignedResponse,
  FileUpdate,
  FileComplete,
  CompleteResponse,
} from '@/types/api';

interface FilesState {
  files: FileResponse[];
  uploadProgress: Map<string, number>;
  processingProgress: Map<string, number>;
  isLoading: boolean;
  isUploading: boolean;
  error: string | null;

  // Actions
  fetchFiles: () => Promise<void>;
  uploadFile: (file: File, metadata: Partial<FilePresigned>) => Promise<string>;
  updateFile: (id: string, data: FileUpdate) => Promise<void>;
  deleteFile: (id: string) => Promise<void>;
  downloadFile: (id: string) => Promise<string>;
  updateFileStatus: (fileId: string, status: FileResponse['status'], progress?: number) => void;
  setUploadProgress: (fileId: string, progress: number) => void;
  clearUploadProgress: (fileId: string) => void;
  clearError: () => void;
  getFileById: (id: string) => FileResponse | undefined;
}

export const useFilesStore = create<FilesState>((set, get) => ({
  files: [],
  uploadProgress: new Map(),
  processingProgress: new Map(),
  isLoading: false,
  isUploading: false,
  error: null,

  fetchFiles: async () => {
    set({ isLoading: true, error: null });
    try {
      const files = await apiClient.get<FileResponse[]>('/files/my-files');
      set({ files, isLoading: false });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch files';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  uploadFile: async (file: File, metadata: Partial<FilePresigned>) => {
    set({ isUploading: true, error: null });
    
    try {
      // Step 1: Get presigned URL
      const fileExtension = file.name.split('.').pop()?.toLowerCase() as FilePresigned['extension'];
      
      if (!fileExtension || !['pdf', 'txt', 'md', 'xls', 'xlsx'].includes(fileExtension)) {
        throw new Error('Unsupported file type');
      }

      const presignedData: FilePresigned = {
        name: metadata.name || file.name.replace(/\.[^/.]+$/, ''), // Remove extension
        extension: fileExtension,
        description: metadata.description,
        size_bytes: file.size,
      };

      const presigned = await apiClient.post<PresignedResponse>(
        '/files/presigned-upload',
        presignedData
      );

      const fileId = presigned.file_id;

      // Add file to list immediately with pending status
      const newFile: FileResponse = {
        id: fileId,
        name: presignedData.name,
        extension: fileExtension,
        size_bytes: file.size,
        description: presignedData.description || null,
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        deleted_at: null,
      };

      set((state) => ({
        files: [newFile, ...state.files],
      }));

      // Step 2: Upload to S3
      const formData = new FormData();
      
      // Add fields if present
      if (presigned.upload.fields) {
        Object.entries(presigned.upload.fields).forEach(([key, value]) => {
          formData.append(key, value);
        });
      }
      
      formData.append('file', file);

      await axios({
        method: presigned.upload.method,
        url: presigned.upload.url,
        data: formData,
        headers: presigned.upload.headers || {},
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            get().setUploadProgress(fileId, progress);
          }
        },
      });

      // Update status to uploaded
      get().updateFileStatus(fileId, 'uploaded');

      // Step 3: Confirm completion
      const completion: FileComplete = { success: true };
      await apiClient.post<CompleteResponse>(
        `/files/upload-completion/${fileId}`,
        completion
      );

      // Clear upload progress
      get().clearUploadProgress(fileId);

      // Refresh files list to get updated file info
      await get().fetchFiles();

      set({ isUploading: false });
      return fileId;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to upload file';
      set({ error: errorMessage, isUploading: false });
      throw error;
    }
  },

  updateFile: async (id: string, data: FileUpdate) => {
    set({ error: null });
    try {
      const updatedFile = await apiClient.patch<FileResponse>(`/files/${id}`, data);
      set((state) => ({
        files: state.files.map((f) => (f.id === id ? updatedFile : f)),
      }));
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to update file';
      set({ error: errorMessage });
      throw error;
    }
  },

  deleteFile: async (id: string) => {
    set({ error: null });
    try {
      await apiClient.delete(`/files/${id}`);
      set((state) => ({
        files: state.files.filter((f) => f.id !== id),
      }));
      
      // Clear any progress maps
      get().clearUploadProgress(id);
      set((state) => {
        const newProcessingProgress = new Map(state.processingProgress);
        newProcessingProgress.delete(id);
        return { processingProgress: newProcessingProgress };
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to delete file';
      set({ error: errorMessage });
      throw error;
    }
  },

  downloadFile: async (id: string) => {
    set({ error: null });
    try {
      // The endpoint returns a presigned URL as a string
      const response = await apiClient.get<any>(`/files/download/${id}`);
      
      // Handle both string response and object response
      const url = typeof response === 'string' ? response : response.url;
      
      if (!url) {
        throw new Error('No download URL received');
      }
      
      return url;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to get download URL';
      set({ error: errorMessage });
      throw error;
    }
  },

  updateFileStatus: (fileId: string, status: FileResponse['status'], progress?: number) => {
    set((state) => {
      const updatedFiles = state.files.map((f) =>
        f.id === fileId ? { ...f, status, ...(progress !== undefined && { progress }), updated_at: new Date().toISOString() } : f
      );

      console.log(`progress: ${progress}`)
      // Update processing progress if provided
      const newProcessingProgress = new Map(state.processingProgress);
      if (progress !== undefined && status === 'processing') {
        newProcessingProgress.set(fileId, progress);
      } else if (status === 'ready' || status === 'error') {
        newProcessingProgress.delete(fileId);
      }

      return { 
        files: updatedFiles,
        processingProgress: newProcessingProgress,
      };
    });
  },

  setUploadProgress: (fileId: string, progress: number) => {
    set((state) => {
      const newProgress = new Map(state.uploadProgress);
      newProgress.set(fileId, progress);
      return { uploadProgress: newProgress };
    });
  },

  clearUploadProgress: (fileId: string) => {
    set((state) => {
      const newProgress = new Map(state.uploadProgress);
      newProgress.delete(fileId);
      return { uploadProgress: newProgress };
    });
  },

  clearError: () => set({ error: null }),

  getFileById: (id: string) => {
    return get().files.find((f) => f.id === id);
  },
}));