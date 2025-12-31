'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Target, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { useJob } from '@/lib/hooks/useJobs';
import { useResumes } from '@/lib/hooks/useResumes';
import { jobsAPI } from '@/lib/api/jobs';
import { matchesAPI } from '@/lib/api/matches';
import { formatDate } from '@/lib/utils';
import { toast } from 'sonner';

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt(params.id as string);
  const { job, isLoading } = useJob(id);
  const { resumes } = useResumes();

  const [matchDialogOpen, setMatchDialogOpen] = useState(false);
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [matching, setMatching] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await jobsAPI.delete(id);
      toast.success('Job deleted successfully');
      router.push('/dashboard/jobs');
    } catch (error) {
      toast.error('Failed to delete job');
    }
  };

  const handleMatch = async () => {
    if (!selectedResumeId) {
      toast.error('Please select a resume');
      return;
    }

    setMatching(true);

    try {
      const response = await matchesAPI.create({
        resume_id: selectedResumeId,
        job_id: id,
        detailed: true,
      });

      toast.success('Match created successfully!');
      setMatchDialogOpen(false);
      router.push(`/dashboard/matches/${response.data.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create match');
    } finally {
      setMatching(false);
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!job) {
    return <div>Job not found</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="flex gap-2">
          <Dialog open={matchDialogOpen} onOpenChange={setMatchDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Target className="h-4 w-4 mr-2" />
                Match with Resume
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Match Job with Resume</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Select Resume</Label>
                  <select
                    className="w-full mt-2 px-3 py-2 border border-input bg-background rounded-md"
                    value={selectedResumeId || ''}
                    onChange={(e) => setSelectedResumeId(parseInt(e.target.value))}
                  >
                    <option value="">Choose a resume...</option>
                    {resumes?.map((resume) => (
                      <option key={resume.id} value={resume.id}>
                        {resume.filename}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  onClick={handleMatch}
                  disabled={!selectedResumeId || matching}
                  className="w-full"
                >
                  {matching ? 'Analyzing...' : 'Create Match'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Job Info */}
      <Card>
        <CardHeader>
          <CardTitle>{job.title}</CardTitle>
          {job.company && (
            <p className="text-muted-foreground">{job.company}</p>
          )}
          <div className="flex gap-2 mt-2">
            <Badge variant={job.is_active ? 'default' : 'secondary'}>
              {job.is_active ? 'Active' : 'Inactive'}
            </Badge>
            <Badge variant="outline">Added {formatDate(job.created_at)}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Description</h3>
            <p className="whitespace-pre-wrap">{job.description}</p>
          </div>

          {job.requirements && (
            <div>
              <h3 className="font-semibold mb-2">Requirements</h3>
              <p className="whitespace-pre-wrap">{job.requirements}</p>
            </div>
          )}

          {job.source_url && (
            <div>
              <h3 className="font-semibold mb-2">Source URL</h3>
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                {job.source_url}
              </a>
            </div>
          )}

          {job.parsed_data?.required_skills && (
            <div>
              <h3 className="font-semibold mb-2">Required Skills (AI Extracted)</h3>
              <div className="flex flex-wrap gap-2">
                {job.parsed_data.required_skills.map((skill: string, idx: number) => (
                  <Badge key={idx} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
