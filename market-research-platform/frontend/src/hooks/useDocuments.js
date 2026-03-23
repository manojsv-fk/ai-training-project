// filepath: market-research-platform/frontend/src/hooks/useDocuments.js
// Custom React hook for document CRUD and upload operations.

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';

export function useDocuments(filters = {}) {
  const queryClient = useQueryClient();

  // ── Fetch all documents ────────────────────────────────────────────────
  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['documents', filters],
    queryFn: () => api.listDocuments(filters),
    refetchInterval: 30000, // Refresh every 30s to catch ingestion status changes
  });

  const documents = data?.documents || [];
  const total = data?.total || 0;

  // ── Upload a new PDF ───────────────────────────────────────────────────
  const uploadMutation = useMutation({
    mutationFn: ({ file, sourceName }) => api.uploadDocument(file, sourceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
    },
  });

  // ── Delete a document ──────────────────────────────────────────────────
  const deleteMutation = useMutation({
    mutationFn: (documentId) => api.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
    },
  });

  return {
    documents,
    total,
    isLoading,
    isError,
    error,
    uploadDocument: (file, sourceName) => uploadMutation.mutate({ file, sourceName }),
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
    deleteDocument: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  };
}
