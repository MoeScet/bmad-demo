import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';

interface UploadResponse {
  job_id: string;
  filename: string;
  file_size: number;
  status: string;
  message: string;
}

interface ManualUploadProps {
  onUploadComplete?: (response: UploadResponse) => void;
  maxFileSize?: number; // in MB
}

export const ManualUpload: React.FC<ManualUploadProps> = ({
  onUploadComplete,
  maxFileSize = 50
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus('error');
      setUploadMessage('Please upload a PDF file');
      return;
    }

    // Validate file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxFileSize) {
      setUploadStatus('error');
      setUploadMessage(`File size must be less than ${maxFileSize}MB`);
      return;
    }

    setUploadedFile(file);
    setIsUploading(true);
    setUploadStatus('uploading');
    setUploadMessage('Uploading file...');
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/upload', {
        method: 'POST',
        body: formData,
        headers: {
          'x-correlation-id': crypto.randomUUID(),
        },
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error?.message || 'Upload failed');
      }

      setUploadStatus('success');
      setUploadMessage('File uploaded successfully! Processing started.');
      setUploadProgress(100);

      if (onUploadComplete) {
        onUploadComplete(result.data);
      }

    } catch (error) {
      setUploadStatus('error');
      setUploadMessage(error instanceof Error ? error.message : 'Upload failed');
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  }, [maxFileSize, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: isUploading
  });

  const resetUpload = () => {
    setUploadStatus('idle');
    setUploadMessage('');
    setUploadProgress(0);
    setUploadedFile(null);
  };

  const getStatusIcon = () => {
    switch (uploadStatus) {
      case 'success':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      case 'uploading':
        return <Upload className="w-6 h-6 text-blue-500 animate-pulse" />;
      default:
        return <FileText className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus) {
      case 'success':
        return 'border-green-300 bg-green-50';
      case 'error':
        return 'border-red-300 bg-red-50';
      case 'uploading':
        return 'border-blue-300 bg-blue-50';
      default:
        return isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 bg-white';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200 ${getStatusColor()}
          ${isUploading ? 'cursor-not-allowed' : 'hover:border-blue-400 hover:bg-blue-50'}
        `}
      >
        <input {...getInputProps()} />

        <div className="space-y-4">
          {getStatusIcon()}

          <div>
            <h3 className="text-lg font-medium text-gray-900">
              {uploadStatus === 'idle' && (isDragActive ? 'Drop the PDF file here' : 'Upload Manual')}
              {uploadStatus === 'uploading' && 'Uploading...'}
              {uploadStatus === 'success' && 'Upload Complete'}
              {uploadStatus === 'error' && 'Upload Failed'}
            </h3>

            <p className="mt-2 text-sm text-gray-600">
              {uploadStatus === 'idle' && 'Drag and drop a PDF manual here, or click to browse'}
              {uploadStatus === 'uploading' && `Processing ${uploadedFile?.name}`}
              {uploadStatus === 'success' && `Successfully uploaded ${uploadedFile?.name}`}
              {uploadStatus === 'error' && uploadMessage}
            </p>
          </div>

          {uploadStatus === 'uploading' && (
            <div className="w-full">
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-gray-500">{uploadProgress}% complete</p>
            </div>
          )}

          {uploadedFile && uploadStatus !== 'uploading' && (
            <div className="mt-4 p-3 bg-gray-100 rounded-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">
                    {uploadedFile.name}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
            </div>
          )}

          {uploadStatus === 'success' && (
            <button
              onClick={resetUpload}
              className="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
            >
              Upload Another File
            </button>
          )}

          {uploadStatus === 'error' && (
            <button
              onClick={resetUpload}
              className="mt-4 px-4 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        <p>• Supported format: PDF files only</p>
        <p>• Maximum file size: {maxFileSize} MB</p>
        <p>• Processing time varies based on file size and content complexity</p>
      </div>
    </div>
  );
};