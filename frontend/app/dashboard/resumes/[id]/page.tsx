'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useResume } from '@/lib/hooks/useResumes';
import { resumesAPI } from '@/lib/api/resumes';
import { formatDate } from '@/lib/utils';
import { toast } from 'sonner';

export default function ResumeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt(params.id as string);
  const { resume, isLoading } = useResume(id);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this resume?')) return;

    try {
      await resumesAPI.delete(id);
      toast.success('Resume deleted successfully');
      router.push('/dashboard/resumes');
    } catch (error) {
      toast.error('Failed to delete resume');
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!resume) {
    return <div>Resume not found</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button variant="destructive" onClick={handleDelete}>
          <Trash2 className="h-4 w-4 mr-2" />
          Delete
        </Button>
      </div>

      {/* Resume Info */}
      <Card>
        <CardHeader>
          <CardTitle>{resume.filename}</CardTitle>
          <div className="flex gap-2 mt-2">
            <Badge>{resume.file_type.toUpperCase()}</Badge>
            <Badge variant="outline">Uploaded {formatDate(resume.created_at)}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Parsed Data */}
          {resume.parsed_data && (
            <div className="space-y-4">
              {resume.parsed_data.name && (
                <div>
                  <h3 className="font-semibold mb-2">Name</h3>
                  <p>{resume.parsed_data.name}</p>
                </div>
              )}

              {resume.parsed_data.email && (
                <div>
                  <h3 className="font-semibold mb-2">Email</h3>
                  <p>{resume.parsed_data.email}</p>
                </div>
              )}

              {resume.parsed_data.skills && resume.parsed_data.skills.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Skills</h3>
                  <div className="flex flex-wrap gap-2">
                    {resume.parsed_data.skills.map((skill: string, idx: number) => (
                      <Badge key={idx} variant="secondary">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Raw Text */}
          <div>
            <h3 className="font-semibold mb-2">Raw Text</h3>
            <div className="p-4 bg-muted rounded-lg max-h-96 overflow-y-auto">
              <pre className="text-sm whitespace-pre-wrap">{resume.raw_text}</pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
