/**
 * Root Theme Component
 *
 * Wraps the entire Docusaurus site to add global components
 * like the ChatWidget that should appear on all pages.
 */

import React from 'react';
import ChatWidget from '@site/src/components/ChatWidget';

interface RootProps {
  children: React.ReactNode;
}

export default function Root({ children }: RootProps): JSX.Element {
  return (
    <>
      {children}
      <ChatWidget />
    </>
  );
}
