"""
Document loader for MDX files from the Docusaurus book.
Extracts content, frontmatter, and structure information.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

import frontmatter
from bs4 import BeautifulSoup
import markdown

logger = logging.getLogger(__name__)


@dataclass
class LoadedDocument:
    """Represents a loaded document with metadata."""
    file_path: str
    module: str
    chapter: str
    title: str
    content: str
    raw_content: str
    content_hash: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    headings: List[Dict[str, Any]] = field(default_factory=list)


class DocumentLoader:
    """
    Loads MDX/MD documents from the Docusaurus docs directory.
    Extracts frontmatter, content, and structural information.
    """

    # Regex patterns
    MDX_IMPORT_PATTERN = re.compile(r'^import\s+.*?;?\s*$', re.MULTILINE)
    MDX_EXPORT_PATTERN = re.compile(r'^export\s+.*?;?\s*$', re.MULTILINE)
    JSX_COMPONENT_PATTERN = re.compile(r'<[A-Z][a-zA-Z]*[^>]*>.*?</[A-Z][a-zA-Z]*>', re.DOTALL)
    ADMONITION_PATTERN = re.compile(r':::(note|tip|info|warning|danger|caution)\s*(.*?)\n(.*?):::', re.DOTALL)
    MERMAID_PATTERN = re.compile(r'```mermaid\n(.*?)```', re.DOTALL)

    def __init__(self, docs_path: str):
        """
        Initialize the document loader.

        Args:
            docs_path: Path to the docs directory
        """
        self.docs_path = Path(docs_path)
        if not self.docs_path.exists():
            raise ValueError(f"Docs path does not exist: {docs_path}")

    def load_all_documents(self) -> List[LoadedDocument]:
        """
        Load all MDX/MD documents from the docs directory.

        Returns:
            List of loaded documents
        """
        documents = []

        # Find all .mdx and .md files
        for ext in ['*.mdx', '*.md']:
            for file_path in self.docs_path.rglob(ext):
                try:
                    doc = self.load_document(file_path)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {self.docs_path}")
        return documents

    def load_document(self, file_path: Path) -> Optional[LoadedDocument]:
        """
        Load a single document.

        Args:
            file_path: Path to the document

        Returns:
            LoadedDocument or None if loading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            # Parse frontmatter
            post = frontmatter.loads(raw_content)
            fm = dict(post.metadata)
            content = post.content

            # Extract module and chapter from path
            rel_path = file_path.relative_to(self.docs_path)
            parts = rel_path.parts

            module = self._extract_module(parts)
            chapter = self._extract_chapter(parts, fm)
            title = fm.get('title', file_path.stem.replace('-', ' ').title())

            # Clean MDX-specific syntax
            cleaned_content = self._clean_mdx_content(content)

            # Extract headings for structure
            headings = self._extract_headings(cleaned_content)

            # Calculate content hash
            content_hash = hashlib.sha256(cleaned_content.encode()).hexdigest()[:16]

            return LoadedDocument(
                file_path=str(rel_path),
                module=module,
                chapter=chapter,
                title=title,
                content=cleaned_content,
                raw_content=raw_content,
                content_hash=content_hash,
                frontmatter=fm,
                headings=headings,
            )

        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            return None

    def _extract_module(self, path_parts: tuple) -> str:
        """Extract module name from path."""
        for part in path_parts:
            if part.startswith('module-'):
                return part
        return 'general'

    def _extract_chapter(self, path_parts: tuple, frontmatter: dict) -> str:
        """Extract chapter name from path or frontmatter."""
        # Try frontmatter first
        if 'sidebar_position' in frontmatter:
            return f"chapter-{frontmatter['sidebar_position']}"

        # Try to extract from filename
        filename = path_parts[-1] if path_parts else ''
        match = re.match(r'chapter-?(\d+)', filename, re.IGNORECASE)
        if match:
            return f"chapter-{match.group(1)}"

        return filename.replace('.mdx', '').replace('.md', '')

    def _clean_mdx_content(self, content: str) -> str:
        """
        Clean MDX-specific syntax to get plain markdown.

        Args:
            content: Raw MDX content

        Returns:
            Cleaned content suitable for embedding
        """
        # Remove import statements
        content = self.MDX_IMPORT_PATTERN.sub('', content)

        # Remove export statements
        content = self.MDX_EXPORT_PATTERN.sub('', content)

        # Convert admonitions to readable format
        def admonition_replacement(match):
            admon_type = match.group(1).upper()
            title = match.group(2).strip() or admon_type
            body = match.group(3).strip()
            return f"\n**{title}:**\n{body}\n"

        content = self.ADMONITION_PATTERN.sub(admonition_replacement, content)

        # Remove Mermaid diagrams but note their presence
        content = self.MERMAID_PATTERN.sub('[Diagram: See original document]', content)

        # Remove JSX components but keep inner text
        def jsx_replacement(match):
            text = match.group(0)
            # Extract text content from JSX
            soup = BeautifulSoup(text, 'html.parser')
            return soup.get_text(separator=' ').strip()

        content = self.JSX_COMPONENT_PATTERN.sub(jsx_replacement, content)

        # Clean up extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        return content

    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract heading structure from content.

        Args:
            content: Markdown content

        Returns:
            List of heading dictionaries with level, text, and position
        """
        headings = []
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        for match in heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({
                'level': level,
                'text': text,
                'position': match.start(),
            })

        return headings

    def get_module_structure(self) -> Dict[str, List[str]]:
        """
        Get the structure of modules and their documents.

        Returns:
            Dictionary mapping module names to document paths
        """
        structure = {}

        for doc in self.load_all_documents():
            if doc.module not in structure:
                structure[doc.module] = []
            structure[doc.module].append(doc.file_path)

        return structure
