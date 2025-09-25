# 🔧 Document ID Mismatch Issue

## Problem
The frontend shows documents with IDs like `7465fb3c6d63c82f` but these don't exist in the database.

## Diagnosis Steps

1. **Clear browser cache and localStorage**:
   ```javascript
   // Run in browser console
   localStorage.clear();
   location.reload();
   ```

2. **Upload a NEW document** and check if it works with the buttons

3. **Check what the /uploads endpoint actually returns**:
   ```javascript
   // Run in browser console
   const token = localStorage.getItem('access_token');
   fetch('https://api.mapmystandards.ai/api/user/intelligence-simple/uploads', {
     headers: {'Authorization': `Bearer ${token}`}
   }).then(r => r.json()).then(data => {
     console.log('Documents from API:', data);
     if (data.evidence) {
       data.evidence.forEach(doc => {
         console.log(`ID: ${doc.id}, Filename: ${doc.filename}`);
       });
     }
   });
   ```

## Root Cause
The `/uploads` endpoint might be returning documents from a different storage system (file-based) while the new endpoints expect database IDs.

## Solution
We need to ensure all documents are properly stored in the database with correct IDs.