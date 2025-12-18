"""
Semantic chunker for splitting documents into meaningful sections.
Preserves context and handles code blocks, tables, and lists.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""
    chunk_id: str
    document_path: str
    module: str
    chapter: str
    section: str
    content: str
    chunk_type: str  # text, code, table, list, mixed
    chunk_index: int
    total_chunks: int
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticChunker:
    """
    Splits documents into semantic chunks suitable for embedding.

    Features:
    - Respects heading boundaries
    - Keeps code blocks intact
    - Handles tables and lists
    - Maintains context with overlap
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Overlap between chunks for context
            min_chunk_size: Minimum chunk size to avoid tiny chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Patterns for content detection
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```[\w]*\n[\s\S]*?```', re.MULTILINE)
        self.table_pattern = re.compile(r'^\|.+\|$(\n\|.+\|$)+', re.MULTILINE)
        self.list_pattern = re.compile(r'^(\s*[-*+]|\s*\d+\.)\s+.+(\n(\s*[-*+]|\s*\d+\.)\s+.+)*', re.MULTILINE)

    def chunk_document(
        self,
        content: str,
        document_path: str,
        module: str,
        chapter: str,
        title: str,
    ) -> List[DocumentChunk]:
        """
        Split a document into chunks.

        Args:
            content: Document content
            document_path: Path to the source document
            module: Module name
            chapter: Chapter name
            title: Document title

        Returns:
            List of DocumentChunk objects
        """
        # First, split by major sections (h1, h2)
        sections = self._split_by_sections(content)

        chunks = []
        chunk_index = 0

        for section_heading, section_content in sections:
            # Split section into smaller chunks if needed
            section_chunks = self._split_section(section_content)

            for chunk_content in section_chunks:
                if len(chunk_content.strip()) < self.min_chunk_size:
                    continue

                # Determine chunk type
                chunk_type = self._detect_chunk_type(chunk_content)

                # Generate unique chunk ID
                chunk_id = self._generate_chunk_id(document_path, chunk_index)

                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_path=document_path,
                    module=module,
                    chapter=chapter,
                    section=section_heading or title,
                    content=chunk_content.strip(),
                    chunk_type=chunk_type,
                    chunk_index=chunk_index,
                    total_chunks=0,  # Will be updated after
                    metadata={
                        'title': title,
                        'has_code': 'code' in chunk_type,
                        'has_table': chunk_type == 'table',
                    }
                )
                chunks.append(chunk)
                chunk_index += 1

        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        logger.info(f"Created {len(chunks)} chunks from {document_path}")
        return chunks

    def _split_by_sections(self, content: str) -> List[tuple]:
        """
        Split content by heading sections.

        Returns:
            List of (heading, content) tuples
        """
        sections = []
        current_heading = None
        current_content = []

        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]
            heading_match = self.heading_pattern.match(line)

            if heading_match and len(heading_match.group(1)) <= 2:  # h1 or h2
                # Save previous section
                if current_content:
                    sections.append((current_heading, '\n'.join(current_content)))

                current_heading = heading_match.group(2).strip()
                current_content = [line]
            else:
                current_content.append(line)

            i += 1

        # Add last section
        if current_content:
            sections.append((current_heading, '\n'.join(current_content)))

        return sections if sections else [(None, content)]

    def _split_section(self, content: str) -> List[str]:
        """
        Split a section into chunks while respecting structure.

        Args:
            content: Section content

        Returns:
            List of chunk strings
        """
        if len(content) <= self.chunk_size:
            return [content]

        chunks = []

        # Find special blocks (code, tables) that shouldn't be split
        special_blocks = []

        # Find code blocks
        for match in self.code_block_pattern.finditer(content):
            special_blocks.append((match.start(), match.end(), 'code'))

        # Find tables
        for match in self.table_pattern.finditer(content):
            special_blocks.append((match.start(), match.end(), 'table'))

        # Sort by position
        special_blocks.sort(key=lambda x: x[0])

        # Split around special blocks
        current_pos = 0
        current_chunk = []
        current_length = 0

        def add_chunk():
            nonlocal current_chunk, current_length
            if current_chunk:
                chunk_text = ''.join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                current_chunk = []
                current_length = 0

        for start, end, block_type in special_blocks:
            # Add text before special block
            text_before = content[current_pos:start]
            if text_before.strip():
                self._add_text_to_chunks(text_before, chunks, current_chunk)

            # Add the special block as its own chunk (or with current if fits)
            block_content = content[start:end]
            if len(block_content) > self.chunk_size:
                # Large code block - keep it whole
                add_chunk()
                chunks.append(block_content)
            else:
                if current_length + len(block_content) > self.chunk_size:
                    add_chunk()
                current_chunk.append(block_content)
                current_length += len(block_content)

            current_pos = end

        # Add remaining text
        remaining = content[current_pos:]
        if remaining.strip():
            self._add_text_to_chunks(remaining, chunks, current_chunk)

        # Add final chunk
        if current_chunk:
            chunks.append(''.join(current_chunk).strip())

        return chunks if chunks else [content]

    def _add_text_to_chunks(
        self,
        text: str,
        chunks: List[str],
        current_chunk: List[str],
    ):
        """Add text to chunks, splitting by paragraphs if needed."""
        paragraphs = text.split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            current_text = ''.join(current_chunk)
            if len(current_text) + len(para) > self.chunk_size:
                # Save current chunk
                if current_text.strip():
                    chunks.append(current_text.strip())
                current_chunk.clear()

                # Add overlap from previous chunk
                if chunks and self.chunk_overlap > 0:
                    overlap = chunks[-1][-self.chunk_overlap:]
                    current_chunk.append(overlap + '\n\n')

            current_chunk.append(para + '\n\n')

    def _detect_chunk_type(self, content: str) -> str:
        """Detect the type of content in a chunk."""
        has_code = bool(self.code_block_pattern.search(content))
        has_table = bool(self.table_pattern.search(content))
        has_list = bool(self.list_pattern.search(content))

        if has_code and has_table:
            return 'mixed'
        elif has_code:
            return 'code'
        elif has_table:
            return 'table'
        elif has_list:
            return 'list'
        else:
            return 'text'

    def _generate_chunk_id(self, document_path: str, chunk_index: int) -> str:
        """Generate a unique chunk ID."""
        content = f"{document_path}:{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Uses simple word-based estimation (actual tokenization varies by model).
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4
