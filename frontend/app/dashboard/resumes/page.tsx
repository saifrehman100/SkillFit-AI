'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FileText, Upload, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useResumes } from '@/lib/hooks/useResumes';
import { resumesAPI } from '@/lib/api/resumes';
import { formatDate } from '@/lib/utils';
import { toast } from 'sonner';

export default function ResumesPage() {
  const { resumes, isLoading, mutate } = useResumes();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<number | null>(null);
  const [matchesCount, setMatchesCount] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  // Calculate user-scoped resume numbers
  const getResumeNumber = (resumeId: number) => {
    if (!resumes) return resumeId;

    const sorted = [...resumes].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    const index = sorted.findIndex(r => r.id === resumeId);
    return index >= 0 ? index + 1 : resumeId;
  };

  const handleDelete = async (id: number) => {
    try {
      // First, get the matches count
      const response = await resumesAPI.getMatchesCount(id);
      const count = response.data.matches_count;

      if (count > 0) {
        // Show confirmation dialog
        setResumeToDelete(id);
        setMatchesCount(count);
        setDeleteDialogOpen(true);
      } else {
        // No matches, delete directly
        if (!confirm('Are you sure you want to delete this resume?')) return;
        await resumesAPI.delete(id, false);
        toast.success('Resume deleted successfully');
        mutate();
      }
    } catch (error) {
      toast.error('Failed to check resume matches');
    }
  };

  const confirmDelete = async (keepMatches: boolean) => {
    if (!resumeToDelete) return;

    setIsDeleting(true);
    try {
      await resumesAPI.delete(resumeToDelete, keepMatches);
      toast.success(
        keepMatches
          ? 'Resume archived successfully. Matches are preserved.'
          : 'Resume and all matches deleted successfully'
      );
      mutate();
      setDeleteDialogOpen(false);
      setResumeToDelete(null);
    } catch (error) {
      toast.error('Failed to delete resume');
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return <div>Loading resumes...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold">Resumes</h1>
          <p className="text-muted-foreground mt-2">
            Manage your uploaded resumes
          </p>
        </div>
        <Link href="/dashboard/resumes/upload">
          <Button>
            <Upload className="h-4 w-4 mr-2" />
            Upload Resume
          </Button>
        </Link>
      </div>

      {/* Resume List */}
      {resumes && resumes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {resumes.map((resume) => (
            <Card key={resume.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 min-w-0 flex-1 overflow-hidden">
                    <FileText className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm text-muted-foreground mb-1">Resume #{getResumeNumber(resume.id)}</div>
                      <CardTitle className="text-lg break-words overflow-wrap-anywhere">{resume.filename}</CardTitle>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(resume.id)}
                    className="text-muted-foreground hover:text-destructive transition-colors shrink-0"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Badge variant="secondary">{resume.file_type.toUpperCase()}</Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  Uploaded {formatDate(resume.created_at)}
                </div>
                {resume.parsed_data && (
                  <div className="text-sm">
                    <p className="font-medium mb-2">Skills Detected:</p>
                    <div className="flex flex-wrap gap-1">
                      {resume.parsed_data.skills?.slice(0, 5).map((skill: string, idx: number) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                      {resume.parsed_data.skills?.length > 5 && (
                        <Badge variant="outline" className="text-xs">
                          +{resume.parsed_data.skills.length - 5} more
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
                <Link href={`/dashboard/resumes/${resume.id}`}>
                  <Button variant="outline" size="sm" className="w-full">
                    View Details
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No resumes yet</h3>
            <p className="text-muted-foreground mb-4 text-center">
              Upload your first resume to get started with AI-powered matching
            </p>
            <Link href="/dashboard/resumes/upload">
              <Button>
                <Upload className="h-4 w-4 mr-2" />
                Upload Resume
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Resume with Matches</DialogTitle>
            <DialogDescription>
              This resume has {matchesCount} match{matchesCount !== 1 ? 'es' : ''} associated with it.
              What would you like to do?
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <p className="text-sm text-muted-foreground">
              If you keep the matches, the resume will be archived but the match data
              (including cover letters, interview prep, and optimized resumes) will be preserved.
            </p>
            <div className="flex flex-col gap-2">
              <Button
                onClick={() => confirmDelete(true)}
                disabled={isDeleting}
                className="w-full"
                variant="default"
              >
                {isDeleting ? 'Deleting...' : 'Keep Matches (Archive Resume)'}
              </Button>
              <Button
                onClick={() => confirmDelete(false)}
                disabled={isDeleting}
                className="w-full"
                variant="destructive"
              >
                {isDeleting ? 'Deleting...' : 'Delete Everything'}
              </Button>
              <Button
                onClick={() => setDeleteDialogOpen(false)}
                disabled={isDeleting}
                className="w-full"
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
