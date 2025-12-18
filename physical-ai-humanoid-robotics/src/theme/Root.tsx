/**
 * Root Theme Component
 *
 * Wraps the entire Docusaurus site to add global components.
 * Includes the RAG-powered chatbot with text selection support.
 */

import React from 'react';
import RAGChatWidget from '@site/src/components/RAGChatWidget';

interface RootProps {
  children: React.ReactNode;
}

export default function Root({ children }: RootProps): JSX.Element {
  return (
    <>
      {children}
      <RAGChatWidget />
    </>
  );
}
