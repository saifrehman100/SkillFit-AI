'use client';

import { FileText, Briefcase, Target, Kanban } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import UsageBanner from '@/components/UsageBanner';
import { useResumes } from '@/lib/hooks/useResumes';
import { useJobs } from '@/lib/hooks/useJobs';
import { useMatches } from '@/lib/hooks/useMatches';
import { useApplications } from '@/lib/hooks/useApplications';
import { formatDate } from '@/lib/utils';

export default function DashboardPage() {
  const { resumes } = useResumes();
  const { jobs } = useJobs();
  const { matches } = useMatches();
  const { applications } = useApplications();

  const avgScore = matches && matches.length > 0
    ? matches.reduce((sum, m) => sum + m.match_score, 0) / matches.length
    : 0;

  const stats = [
    {
      title: 'Total Resumes',
      value: resumes?.length || 0,
      icon: FileText,
      href: '/dashboard/resumes',
      color: 'text-blue-500',
    },
    {
      title: 'Active Jobs',
      value: jobs?.length || 0,
      icon: Briefcase,
      href: '/dashboard/jobs',
      color: 'text-purple-500',
    },
    {
      title: 'Matches',
      value: matches?.length || 0,
      icon: Target,
      href: '/dashboard/matches',
      color: 'text-green-500',
    },
    {
      title: 'Applications',
      value: applications?.length || 0,
      icon: Kanban,
      href: '/dashboard/applications',
      color: 'text-orange-500',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-3xl font-heading font-bold">Welcome Back!</h1>
        <p className="text-muted-foreground mt-2">
          Here&apos;s what&apos;s happening with your job search
        </p>
      </div>

      {/* Usage Banner */}
      <UsageBanner />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Link key={stat.title} href={stat.href}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <Icon className={`h-5 w-5 ${stat.color}`} />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{stat.value}</div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Average Match Score */}
      {matches && matches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Average Match Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{avgScore.toFixed(1)}%</div>
            <p className="text-sm text-muted-foreground mt-2">
              Based on {matches.length} {matches.length === 1 ? 'match' : 'matches'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <Link href="/dashboard/resumes/upload">
            <Button>Upload Resume</Button>
          </Link>
          <Link href="/dashboard/jobs/create">
            <Button variant="outline">Add Job</Button>
          </Link>
          <Link href="/dashboard/applications">
            <Button variant="outline">Track Application</Button>
          </Link>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      {matches && matches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Matches</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {matches.slice(0, 5).map((match) => (
                <Link
                  key={match.id}
                  href={`/dashboard/matches/${match.id}`}
                  className="block p-4 rounded-lg border border-border hover:bg-accent transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Match #{match.id}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(match.created_at)}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${
                        match.match_score >= 80 ? 'text-green-500' :
                        match.match_score >= 60 ? 'text-yellow-500' :
                        'text-red-500'
                      }`}>
                        {match.match_score.toFixed(0)}%
                      </div>
                      <p className="text-xs text-muted-foreground">Match Score</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
