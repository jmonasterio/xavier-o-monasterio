#!/bin/bash
# Safely rebuild the site
# Clears generated files (preserves photos/, gallery.json, index.html, search-worker.js)
# Then rebuilds site structure and search index

set -e

echo "Clearing generated files..."
rm -rf site/papers
rm -f site/tree.json
rm -f site/search-index.json
rm -f site/*.md

echo "Building site..."
python3 build.py

echo "Building search index..."
python3 build-search-index.py

echo "Done!"
