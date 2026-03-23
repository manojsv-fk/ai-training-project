// filepath: market-research-platform/frontend/src/pages/Documents.jsx
// Document management page with upload and list components.

import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import DocumentUpload from '../components/documents/DocumentUpload';
import DocumentList from '../components/documents/DocumentList';

function Documents() {
  const queryClient = useQueryClient();
  const [selectedDoc, setSelectedDoc] = useState(null);

  const handleUploadSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['documents'] });
    queryClient.invalidateQueries({ queryKey: ['documents-feed'] });
    queryClient.invalidateQueries({ queryKey: ['status'] });
  };

  const handleDocumentSelect = (doc) => {
    setSelectedDoc(doc);
  };

  return (
    <div className="documents-page">
      <header className="documents-page__header">
        <h1>Documents</h1>
        <p>Upload industry reports and manage your research corpus.</p>
      </header>

      <DocumentUpload onUploadSuccess={handleUploadSuccess} />
      <DocumentList onSelect={handleDocumentSelect} />
    </div>
  );
}

export default Documents;
