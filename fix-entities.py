#!/usr/bin/env python3
"""
Fix HTML entities in markdown files.
Converts &apos; to ' across all markdown files in xavier-papers-organized/
"""

import os
from pathlib import Path

def fix_entities_in_file(filepath):
    """Fix HTML entities in a single file. Returns count of replacements."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count occurrences
    count = content.count('&apos;') + content.count('&nbsp;')

    if count > 0:
        # Replace entities
        fixed = content.replace('&apos;', "'").replace('&nbsp;', ' ')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed)

    return count

def main():
    dirs = [Path('xavier-papers-organized'), Path('.')]
    total_fixed = 0
    files_modified = 0
    seen = set()

    for base_dir in dirs:
        for md_file in base_dir.rglob('*.md'):
            if md_file.resolve() in seen or 'site/' in str(md_file):
                continue
            seen.add(md_file.resolve())
            count = fix_entities_in_file(md_file)
            if count > 0:
                print(f"Fixed {count} entities in {md_file}")
                total_fixed += count
                files_modified += 1

    print(f"\nTotal: Fixed {total_fixed} entities in {files_modified} files")

if __name__ == '__main__':
    main()
