#!/bin/bash

# Update all references from upload-enhanced.html to upload-enhanced-v2.html
echo "Updating upload links in all HTML files..."

# Find and replace in all HTML files
find web -name "*.html" -type f | while read -r file; do
    if grep -q "upload-enhanced.html" "$file"; then
        echo "Updating: $file"
        # Use sed with backup
        sed -i.bak 's/upload-enhanced\.html/upload-enhanced-v2.html/g' "$file"
    fi
done

echo "Update complete!"
echo "Backup files created with .bak extension"

# Show summary
echo -e "\nFiles updated:"
find web -name "*.html" -type f | while read -r file; do
    if grep -q "upload-enhanced-v2.html" "$file"; then
        echo "  - $file"
    fi
done