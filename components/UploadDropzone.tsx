'use client';

import React, { useState, useRef, useCallback } from 'react';

interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
  documentId?: string;
}

interface UploadDropzoneProps {
  onUploadComplete?: (documentId: string, file: File) => void;
  onUploadError?: (error: string, file: File) => void;
  maxFileSize?: number;
  acceptedFileTypes?: string[];
  apiEndpoint?: string;
}

export default function UploadDropzone({
  onUploadComplete,
  onUploadError,
  maxFileSize = 100 * 1024 * 1024, // 100MB default
  acceptedFileTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'application/msword',
    'text/plain',
    'text/csv',
  ],
  apiEndpoint = process.env.NEXT_PUBLIC_API_URL || 'https://api.mapmystandards.ai',
}: UploadDropzoneProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const generateFileId = () => Math.random().toString(36).substring(7);

  const validateFile = (file: File): string | null => {
    if (file.size > maxFileSize) {
      return `File size exceeds ${maxFileSize / (1024 * 1024)}MB limit`;
    }
    
    if (!acceptedFileTypes.includes(file.type)) {
      return 'File type not supported';
    }
    
    return null;
  };

  const uploadFile = async (uploadFile: UploadFile) => {
    const { file, id } = uploadFile;
    
    try {
      // Update status to uploading
      setFiles(prev => prev.map(f => 
        f.id === id ? { ...f, status: 'uploading' as const } : f
      ));

      // Step 1: Get presigned URL
      const presignResponse = await fetch(`${apiEndpoint}/upload/presign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        credentials: 'include',
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type,
          file_size: file.size,
        }),
      });

      if (!presignResponse.ok) {
        throw new Error('Failed to get upload URL');
      }

      const presignData = await presignResponse.json();

      // Step 2: Upload to S3 using presigned POST
      const formData = new FormData();
      Object.entries(presignData.upload_fields).forEach(([key, value]) => {
        formData.append(key, value as string);
      });
      formData.append('file', file);

      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          setFiles(prev => prev.map(f => 
            f.id === id ? { ...f, progress } : f
          ));
        }
      });

      // Handle upload completion
      await new Promise((resolve, reject) => {
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(xhr.response);
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed'));
        });

        xhr.open('POST', presignData.upload_url);
        xhr.send(formData);
      });

      // Step 3: Complete upload
      const completeResponse = await fetch(`${apiEndpoint}/upload/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        credentials: 'include',
        body: JSON.stringify({
          file_key: presignData.file_key,
          filename: file.name,
          file_size: file.size,
          content_type: file.type,
        }),
      });

      if (!completeResponse.ok) {
        throw new Error('Failed to complete upload');
      }

      const documentData = await completeResponse.json();

      // Update file status to complete
      setFiles(prev => prev.map(f => 
        f.id === id 
          ? { ...f, status: 'complete' as const, progress: 100, documentId: documentData.id }
          : f
      ));

      if (onUploadComplete) {
        onUploadComplete(documentData.id, file);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      
      setFiles(prev => prev.map(f => 
        f.id === id 
          ? { ...f, status: 'error' as const, error: errorMessage }
          : f
      ));

      if (onUploadError) {
        onUploadError(errorMessage, file);
      }
    }
  };

  const handleFiles = useCallback((fileList: FileList) => {
    const newFiles: UploadFile[] = [];

    Array.from(fileList).forEach(file => {
      const error = validateFile(file);
      
      const uploadFile: UploadFile = {
        id: generateFileId(),
        file,
        progress: 0,
        status: error ? 'error' : 'pending',
        error,
      };

      newFiles.push(uploadFile);

      if (!error) {
        // Start upload immediately
        setTimeout(() => uploadFile(uploadFile), 0);
      }
    });

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept={acceptedFileTypes.join(',')}
        />

        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-4"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        <p className="text-lg font-medium text-gray-900 mb-2">
          Drop files here or click to upload
        </p>
        <p className="text-sm text-gray-500">
          Supported formats: PDF, Word, Excel, CSV, Text
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Maximum file size: {maxFileSize / (1024 * 1024)}MB
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          {files.map(file => (
            <div
              key={file.id}
              className="border rounded-lg p-4 bg-white shadow-sm"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.file.size)}
                  </p>
                </div>
                
                {file.status === 'complete' && (
                  <svg
                    className="h-5 w-5 text-green-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
                
                {file.status === 'error' && (
                  <button
                    onClick={() => removeFile(file.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                )}
              </div>

              {file.status === 'uploading' && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${file.progress}%` }}
                  />
                </div>
              )}

              {file.error && (
                <p className="text-xs text-red-600 mt-2">{file.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}