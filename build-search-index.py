#!/usr/bin/env python3
"""
Build search index for Lunr.js full-text search.
This is separate from the main site build to allow independent updates.

Usage: python build-search-index.py
Output: site/search-index.json
"""

import os
import json
import re
from pathlib import Path

PAPERS_DIR = Path("xavier-papers-organized")
OUTPUT_FILE = Path("site/search-index.json")

def strip_frontmatter(content):
    """Remove YAML frontmatter from markdown content."""
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            return content[end + 3:].strip()
    return content

def extract_title_from_frontmatter(content):
    """Extract title from YAML frontmatter if present."""
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            frontmatter = content[3:end]
            for line in frontmatter.split('\n'):
                if line.startswith('title:'):
                    title = line[6:].strip()
                    # Remove quotes if present
                    if (title.startswith('"') and title.endswith('"')) or \
                       (title.startswith("'") and title.endswith("'")):
                        title = title[1:-1]
                    return title
    return None

def extract_first_heading(content):
    """Extract first # heading from content."""
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return None

def clean_text(text):
    """Clean markdown text for indexing."""
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove markdown formatting
    text = re.sub(r'[*_`#]', '', text)
    # Remove horizontal rules
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_document_path(file_path):
    """Convert file path to URL path used in the site."""
    # Remove the papers directory prefix and convert to site path
    rel_path = file_path.relative_to(PAPERS_DIR)
    return f"writings/{rel_path}"

def build_index():
    """Build search index from all markdown files."""
    documents = []
    doc_id = 0

    for md_file in PAPERS_DIR.rglob("*.md"):
        # Skip notes files
        if md_file.name.endswith('.notes.md'):
            continue

        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
            continue

        # Extract title
        title = extract_title_from_frontmatter(content)
        if not title:
            title = extract_first_heading(strip_frontmatter(content))
        if not title:
            title = md_file.stem.replace('-', ' ').title()

        # Clean content for indexing
        body = strip_frontmatter(content)
        body = clean_text(body)

        # Get URL path
        url_path = get_document_path(md_file)

        # Get folder/category for display
        parts = md_file.relative_to(PAPERS_DIR).parts
        if len(parts) > 1:
            category = parts[0].replace('-', ' ').title()
        else:
            category = "Writings"

        documents.append({
            "id": doc_id,
            "title": title,
            "body": body,
            "path": url_path,
            "category": category
        })

        doc_id += 1

    return documents

def main():
    print("Building search index...")

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    documents = build_index()

    # Write the documents for Lunr to index client-side
    # We'll build the actual Lunr index in the browser for simplicity
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2)

    print(f"Indexed {len(documents)} documents")
    print(f"Search index written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
