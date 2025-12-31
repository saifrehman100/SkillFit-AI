'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { resumesAPI } from '@/lib/api/resumes';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

export default function ResumeUploadPage() {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];

    if (!file) return;

    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(file.type)) {
      toast.error('Only PDF, DOCX, and TXT files are supported');
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress (in real app, use axios onUploadProgress)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      await resumesAPI.upload(selectedFile, true);

      clearInterval(progressInterval);
      setUploadProgress(100);

      toast.success('Resume uploaded and analyzed successfully!');
      setTimeout(() => {
        router.push('/dashboard/resumes');
      }, 1000);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed');
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-heading font-bold">Upload Resume</h1>
        <p className="text-muted-foreground mt-2">
          Upload your resume for AI-powered analysis and matching
        </p>
      </div>

      {/* Upload Card */}
      <Card>
        <CardHeader>
          <CardTitle>Select File</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
              isDragActive ? 'border-primary bg-primary/5' : 'border-muted hover:border-primary/50',
              uploading && 'opacity-50 cursor-not-allowed'
            )}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            {isDragActive ? (
              <p className="text-lg font-medium">Drop the file here...</p>
            ) : (
              <>
                <p className="text-lg font-medium mb-2">
                  Drag & drop your resume here
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  or click to select a file
                </p>
                <p className="text-xs text-muted-foreground">
                  Supported formats: PDF, DOCX, TXT (max 10MB)
                </p>
              </>
            )}
          </div>

          {/* Selected File */}
          {selectedFile && (
            <div className="flex items-center justify-between p-4 bg-accent rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-primary" />
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              {!uploading && (
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>
          )}

          {/* Upload Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Uploading and analyzing...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className="flex-1"
            >
              {uploading ? 'Uploading...' : 'Upload & Analyze'}
            </Button>
            <Button
              variant="outline"
              onClick={() => router.back()}
              disabled={uploading}
            >
              Cancel
            </Button>
          </div>

          {/* Info */}
          <div className="bg-muted/50 p-4 rounded-lg text-sm">
            <p className="font-medium mb-2">What happens next?</p>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Your resume will be parsed using AI</li>
              <li>• Skills and experience will be extracted</li>
              <li>• You can then match it against job descriptions</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
