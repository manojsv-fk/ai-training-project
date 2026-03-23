// filepath: market-research-platform/frontend/src/components/documents/DocumentUpload.jsx
// Drag-and-drop PDF upload component with progress feedback.

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';

function DocumentUpload({ onUploadSuccess }) {
  const { uploadDocument, isUploading } = useDocuments();
  const [uploadStatus, setUploadStatus] = useState(null); // null | 'success' | 'error'
  const [statusMessage, setStatusMessage] = useState('');

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      setUploadStatus('error');
      setStatusMessage('Only PDF files up to 50MB are accepted.');
      setTimeout(() => setUploadStatus(null), 3000);
      return;
    }

    // Upload each accepted file
    acceptedFiles.forEach((file) => {
      uploadDocument(file, '');
      setUploadStatus('success');
      setStatusMessage(`Uploading: ${file.name}`);
      if (onUploadSuccess) {
        setTimeout(onUploadSuccess, 500);
      }
      setTimeout(() => setUploadStatus(null), 3000);
    });
  }, [uploadDocument, onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true,
  });

  return (
    <div className="document-upload">
      <div
        {...getRootProps()}
        className={`document-upload__zone ${isDragActive ? 'document-upload__zone--active' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="document-upload__icon">
          <Upload size={32} />
        </div>
        <p className="document-upload__prompt">
          {isDragActive
            ? 'Drop your PDF files here...'
            : <>Drag & drop PDF reports here, or <span className="document-upload__link">browse</span></>
          }
        </p>
        <p className="document-upload__hint">
          Supports: PDF &middot; Max 50 MB per file
        </p>
      </div>

      {isUploading && (
        <div className="document-upload__progress">
          <span className="loading-spinner" style={{ marginRight: 8 }} />
          Processing upload...
        </div>
      )}

      {uploadStatus === 'success' && (
        <div className="document-upload__progress" style={{ color: 'var(--color-success)' }}>
          <CheckCircle size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
          {statusMessage}
        </div>
      )}

      {uploadStatus === 'error' && (
        <div className="document-upload__progress" style={{ color: 'var(--color-danger)' }}>
          <AlertCircle size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
          {statusMessage}
        </div>
      )}
    </div>
  );
}

export default DocumentUpload;
