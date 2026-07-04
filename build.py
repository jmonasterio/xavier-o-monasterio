#!/usr/bin/env python3
"""
Build script for Xavier Ortiz Monasterio Papers static site.

Scans xavier-papers-organized/, generates tree index, copies files to /site.
"""

import os
import json
import shutil
from pathlib import Path

# Configuration
SOURCE_DIR = Path("xavier-papers-organized")
SITE_DIR = Path("site")
PAPERS_DIR = SITE_DIR / "papers"

# Files to include from root
ROOT_FILES = ["biography.md", "CURATORS-NOTE.md", "OVERVIEW-FOR-COLLEAGUES.md", "LICENSE.md"]

def get_notes_content(md_path):
    """Read the .notes file for a markdown file if it exists."""
    notes_path = md_path.with_suffix('.notes')
    if notes_path.exists():
        return notes_path.read_text(encoding='utf-8', errors='replace')
    return None

def extract_title_from_md(md_path):
    """Extract title from markdown frontmatter or first heading."""
    try:
        content = md_path.read_text(encoding='utf-8', errors='replace')
        lines = content.split('\n')

        # Check for YAML frontmatter
        if lines[0].strip() == '---':
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    break
                if line.startswith('title:'):
                    title = line.split(':', 1)[1].strip().strip('"\'')
                    return title

        # Look for first heading
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
            if line.startswith('## '):
                return line[3:].strip()

        return None
    except:
        return None

def extract_date_from_notes(notes_content):
    """Extract date from notes content."""
    if not notes_content:
        return None
    for line in notes_content.split('\n'):
        if line.startswith('**Date:**') or line.startswith('**Full date:**'):
            return line.split(':', 1)[1].strip()
    return None

def build_tree():
    """Build the file tree structure."""
    tree = {
        "years": {},
        "special": {},  # book-manuscript, bibliography
        "appendix": {}  # course-materials, exams, personal, uncategorized
    }

    if not SOURCE_DIR.exists():
        print(f"Error: {SOURCE_DIR} not found")
        return tree

    for item in sorted(SOURCE_DIR.iterdir()):
        if not item.is_dir():
            continue

        folder_name = item.name

        # Handle appendix specially (has subfolders)
        if folder_name == 'appendix':
            for subfolder in sorted(item.iterdir()):
                if not subfolder.is_dir():
                    continue
                files = []
                for md_file in sorted(subfolder.glob("*.md")):
                    if md_file.name.endswith('.notes') or md_file.name == 'README.md':
                        continue
                    notes_content = get_notes_content(md_file)
                    title = extract_title_from_md(md_file)
                    date = extract_date_from_notes(notes_content)
                    files.append({
                        "name": md_file.name,
                        "path": f"appendix/{subfolder.name}/{md_file.name}",
                        "title": title,
                        "date": date,
                        "has_notes": notes_content is not None
                    })
                if files:
                    tree["appendix"][subfolder.name] = files
            continue

        files = []

        # Get all .md files (excluding .notes and README)
        for md_file in sorted(item.glob("*.md")):
            if md_file.name.endswith('.notes') or md_file.name == 'README.md':
                continue

            notes_content = get_notes_content(md_file)
            title = extract_title_from_md(md_file)
            date = extract_date_from_notes(notes_content)

            files.append({
                "name": md_file.name,
                "path": f"{folder_name}/{md_file.name}",
                "title": title,
                "date": date,
                "has_notes": notes_content is not None
            })

        if not files:
            continue

        # Categorize by year vs special folders
        if folder_name.isdigit():
            tree["years"][folder_name] = files
        else:
            tree["special"][folder_name] = files

    return tree

def copy_papers():
    """Copy markdown and notes files to site/papers/."""
    if PAPERS_DIR.exists():
        shutil.rmtree(PAPERS_DIR)

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)

    file_count = 0

    for item in SOURCE_DIR.iterdir():
        if not item.is_dir():
            continue

        # Handle appendix specially (has subfolders)
        if item.name == 'appendix':
            appendix_dir = PAPERS_DIR / 'appendix'
            appendix_dir.mkdir(exist_ok=True)
            for subfolder in item.iterdir():
                if not subfolder.is_dir():
                    continue
                dest_subfolder = appendix_dir / subfolder.name
                dest_subfolder.mkdir(exist_ok=True)
                for f in subfolder.glob("*"):
                    if f.suffix in ['.md', '.notes'] and f.name != 'README.md':
                        shutil.copy2(f, dest_subfolder / f.name)
                        if f.suffix == '.md':
                            file_count += 1
            continue

        dest_folder = PAPERS_DIR / item.name
        dest_folder.mkdir(exist_ok=True)

        # Copy .md and .notes files
        for f in item.glob("*"):
            if f.suffix in ['.md', '.notes'] and f.name != 'README.md':
                shutil.copy2(f, dest_folder / f.name)
                if f.suffix == '.md':
                    file_count += 1

    return file_count

def copy_root_files():
    """Copy root markdown files to site/."""
    for filename in ROOT_FILES:
        src = Path(filename)
        if src.exists():
            shutil.copy2(src, SITE_DIR / filename)
            print(f"  Copied {filename}")

def write_tree_json(tree):
    """Write tree structure to JSON file."""
    tree_path = SITE_DIR / "tree.json"
    with open(tree_path, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2)
    print(f"  Generated tree.json ({len(tree['years'])} years, {len(tree['special'])} special folders)")

def main():
    print("Building Xavier Ortiz Monasterio Papers site...")
    print()

    # Ensure site directory exists
    SITE_DIR.mkdir(exist_ok=True)

    # Build tree
    print("1. Scanning folder structure...")
    tree = build_tree()
    write_tree_json(tree)

    # Copy papers
    print("2. Copying papers...")
    file_count = copy_papers()
    print(f"  Copied {file_count} markdown files")

    # Copy root files
    print("3. Copying root files...")
    copy_root_files()

    # Summary
    total_years = len(tree['years'])
    total_special = len(tree['special'])
    total_files = sum(len(files) for files in tree['years'].values())
    total_files += sum(len(files) for files in tree['special'].values())

    print()
    print("Build complete!")
    print(f"  {total_years} year folders")
    print(f"  {total_special} special folders")
    print(f"  {total_files} documents indexed")
    print(f"  Output: {SITE_DIR.absolute()}")

if __name__ == "__main__":
    main()
