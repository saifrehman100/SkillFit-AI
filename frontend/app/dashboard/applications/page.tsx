'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useApplications } from '@/lib/hooks/useApplications';
import { applicationsAPI } from '@/lib/api/applications';
import { formatDate, getStatusColor, capitalizeFirst } from '@/lib/utils';
import { toast } from 'sonner';

const statuses = ['wishlist', 'applied', 'interview', 'offer', 'rejected'] as const;

export default function ApplicationsPage() {
  const { applications, mutate } = useApplications();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    company: '',
    position: '',
    status: 'wishlist' as typeof statuses[number],
    job_url: '',
    notes: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.company || !formData.position) {
      toast.error('Company and position are required');
      return;
    }

    try {
      await applicationsAPI.create(formData);
      toast.success('Application added successfully');
      setDialogOpen(false);
      setFormData({
        company: '',
        position: '',
        status: 'wishlist',
        job_url: '',
        notes: '',
      });
      mutate();
    } catch (error: any) {
      console.error('Application creation error:', error);

      // Handle validation errors (422)
      if (error?.response?.data?.detail) {
        const detail = error.response.data.detail;

        // If detail is an array of validation errors
        if (Array.isArray(detail)) {
          const messages = detail.map((err: any) => {
            const field = err.loc?.slice(-1)[0] || 'field';
            return `${field}: ${err.msg}`;
          }).join(', ');
          toast.error(`Validation error: ${messages}`);
        } else if (typeof detail === 'string') {
          toast.error(detail);
        } else {
          toast.error('Failed to create application');
        }
      } else {
        toast.error('Failed to create application');
      }
    }
  };

  const handleStatusChange = async (id: number, newStatus: typeof statuses[number]) => {
    try {
      await applicationsAPI.update(id, { status: newStatus });
      toast.success('Status updated');
      mutate();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const groupedApplications = statuses.reduce((acc, status) => {
    acc[status] = applications?.filter((app) => app.status === status) || [];
    return acc;
  }, {} as Record<typeof statuses[number], Array<any>>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold">Applications</h1>
          <p className="text-muted-foreground mt-2">
            Track your job applications through the hiring process
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Application
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Application</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="company">Company *</Label>
                <Input
                  id="company"
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="position">Position *</Label>
                <Input
                  id="position"
                  value={formData.position}
                  onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  className="w-full mt-2 px-3 py-2 border border-input bg-background rounded-md"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as typeof statuses[number] })}
                >
                  {statuses.map((status) => (
                    <option key={status} value={status}>
                      {capitalizeFirst(status)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="job_url">Job URL</Label>
                <Input
                  id="job_url"
                  type="url"
                  value={formData.job_url}
                  onChange={(e) => setFormData({ ...formData, job_url: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                />
              </div>
              <Button type="submit" className="w-full">
                Add Application
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {statuses.map((status) => (
          <div key={status} className="space-y-4">
            <Card className="bg-muted/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center justify-between">
                  <span>{capitalizeFirst(status)}</span>
                  <Badge variant="secondary">{groupedApplications[status].length}</Badge>
                </CardTitle>
              </CardHeader>
            </Card>

            {groupedApplications[status].map((app) => (
              <Card key={app.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4 space-y-3">
                  <div>
                    <h4 className="font-semibold">{app.company}</h4>
                    <p className="text-sm text-muted-foreground">{app.position}</p>
                  </div>
                  {app.notes && (
                    <p className="text-xs text-muted-foreground line-clamp-2">{app.notes}</p>
                  )}
                  <div className="text-xs text-muted-foreground">
                    {formatDate(app.created_at)}
                  </div>
                  <select
                    className="w-full text-xs px-2 py-1 border border-input bg-background rounded"
                    value={app.status}
                    onChange={(e) => handleStatusChange(app.id, e.target.value as typeof statuses[number])}
                  >
                    {statuses.map((s) => (
                      <option key={s} value={s}>
                        {capitalizeFirst(s)}
                      </option>
                    ))}
                  </select>
                </CardContent>
              </Card>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
