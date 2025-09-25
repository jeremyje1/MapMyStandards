#!/bin/bash
# Debug why specific documents are returning 404

echo "🔍 Debugging document issues..."
echo ""
echo "To debug, we need to:"
echo "1. Check if the document exists in the database"
echo "2. Verify the user_id matches"
echo ""
echo "Run this SQL query in Railway to check the document:"
echo ""
cat << 'EOF'
-- Check if document exists and its user_id
SELECT id, filename, user_id, status, uploaded_at, deleted_at
FROM documents
WHERE id = '7465fb3c6d63c82f';

-- Check all documents to see the pattern
SELECT id, filename, user_id, status, uploaded_at
FROM documents
WHERE deleted_at IS NULL
ORDER BY uploaded_at DESC
LIMIT 20;
EOF