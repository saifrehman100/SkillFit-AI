'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { jobsAPI } from '@/lib/api/jobs';
import { toast } from 'sonner';

export default function CreateJobPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    description: '',
    requirements: '',
    source_url: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title || !formData.description) {
      toast.error('Title and description are required');
      return;
    }

    setLoading(true);

    try {
      await jobsAPI.create(formData, true);
      toast.success('Job created and analyzed successfully!');
      router.push('/dashboard/jobs');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>

      <div>
        <h1 className="text-3xl font-heading font-bold">Add Job</h1>
        <p className="text-muted-foreground mt-2">
          Enter job details to match against your resumes
        </p>
      </div>

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle>Job Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="title">Job Title *</Label>
              <Input
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="e.g., Senior Backend Engineer"
                required
              />
            </div>

            <div>
              <Label htmlFor="company">Company</Label>
              <Input
                id="company"
                name="company"
                value={formData.company}
                onChange={handleChange}
                placeholder="e.g., Tech Corp"
              />
            </div>

            <div>
              <Label htmlFor="description">Job Description *</Label>
              <Textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Paste the full job description here..."
                rows={8}
                required
              />
            </div>

            <div>
              <Label htmlFor="requirements">Requirements</Label>
              <Textarea
                id="requirements"
                name="requirements"
                value={formData.requirements}
                onChange={handleChange}
                placeholder="Specific requirements, qualifications, etc."
                rows={4}
              />
            </div>

            <div>
              <Label htmlFor="source_url">Job URL (LinkedIn, etc.)</Label>
              <Input
                id="source_url"
                name="source_url"
                value={formData.source_url}
                onChange={handleChange}
                placeholder="https://..."
                type="url"
              />
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Creating...' : 'Create & Analyze Job'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                disabled={loading}
              >
                Cancel
              </Button>
            </div>

            <div className="bg-muted/50 p-4 rounded-lg text-sm">
              <p className="font-medium mb-2">What happens next?</p>
              <ul className="space-y-1 text-muted-foreground">
                <li>• AI will extract required skills from the description</li>
                <li>• You can match this job against your resumes</li>
                <li>• Get detailed match scores and recommendations</li>
              </ul>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
