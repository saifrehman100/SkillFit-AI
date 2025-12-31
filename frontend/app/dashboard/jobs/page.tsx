'use client';

import Link from 'next/link';
import { Briefcase, Plus, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useJobs } from '@/lib/hooks/useJobs';
import { jobsAPI } from '@/lib/api/jobs';
import { formatDate } from '@/lib/utils';
import { toast } from 'sonner';

export default function JobsPage() {
  const { jobs, isLoading, mutate } = useJobs();

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await jobsAPI.delete(id);
      toast.success('Job deleted successfully');
      mutate();
    } catch (error) {
      toast.error('Failed to delete job');
    }
  };

  if (isLoading) {
    return <div>Loading jobs...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold">Jobs</h1>
          <p className="text-muted-foreground mt-2">
            Manage job descriptions
          </p>
        </div>
        <Link href="/dashboard/jobs/create">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Job
          </Button>
        </Link>
      </div>

      {/* Job List */}
      {jobs && jobs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {jobs.map((job) => (
            <Card key={job.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 min-w-0 flex-1">
                    <Briefcase className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    <CardTitle className="text-lg break-words">{job.title}</CardTitle>
                  </div>
                  <button
                    onClick={() => handleDelete(job.id)}
                    className="text-muted-foreground hover:text-destructive transition-colors shrink-0"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                {job.company && (
                  <p className="text-sm text-muted-foreground">{job.company}</p>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm line-clamp-3">{job.description}</p>
                <div className="flex items-center justify-between mb-2">
                  <Badge variant={job.is_active ? 'default' : 'secondary'}>
                    {job.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(job.created_at)}
                  </span>
                </div>
                <Link href={`/dashboard/jobs/${job.id}`}>
                  <Button variant="outline" size="sm" className="w-full mt-2">
                    View & Match
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Briefcase className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No jobs yet</h3>
            <p className="text-muted-foreground mb-4 text-center">
              Add a job description to start matching with your resumes
            </p>
            <Link href="/dashboard/jobs/create">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Job
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
