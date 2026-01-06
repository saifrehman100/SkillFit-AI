'use client';

import Link from 'next/link';
import { Target } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useMatches } from '@/lib/hooks/useMatches';
import { formatDate, getScoreColor } from '@/lib/utils';

export default function MatchesPage() {
  const { matches, isLoading } = useMatches();

  // Calculate user-scoped match numbers
  const getMatchNumber = (matchId: number) => {
    if (!matches) return matchId;

    // Sort by created_at ascending (oldest first) to get sequential order
    const sorted = [...matches].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    // Find index (0-based) and add 1 for user-friendly numbering
    const index = sorted.findIndex(m => m.id === matchId);
    return index >= 0 ? index + 1 : matchId;
  };

  if (isLoading) {
    return <div>Loading matches...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-heading font-bold">Matches</h1>
        <p className="text-muted-foreground mt-2">
          View your resume-to-job match results
        </p>
      </div>

      {/* Match List */}
      {matches && matches.length > 0 ? (
        <div className="space-y-4">
          {matches.map((match) => (
            <Link key={match.id} href={`/dashboard/matches/${match.id}`}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="h-5 w-5 text-primary" />
                        <h3 className="font-semibold">Match #{getMatchNumber(match.id)}</h3>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Match Score</p>
                          <p className="font-medium">{match.match_score.toFixed(0)}%</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">ATS Score</p>
                          <p className="font-medium">{match.ats_score ? `${match.ats_score.toFixed(0)}%` : 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Created</p>
                          <p className="font-medium">{formatDate(match.created_at)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Model</p>
                          <p className="font-medium text-xs">{match.llm_model || 'N/A'}</p>
                        </div>
                      </div>
                      {match.missing_skills && match.missing_skills.length > 0 && (
                        <div className="mt-4">
                          <p className="text-sm text-muted-foreground mb-2">Missing Skills:</p>
                          <div className="flex flex-wrap gap-1">
                            {match.missing_skills.slice(0, 5).map((skill, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                            {match.missing_skills.length > 5 && (
                              <Badge variant="outline" className="text-xs">
                                +{match.missing_skills.length - 5} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="text-right ml-6">
                      <div className={`text-5xl font-bold ${getScoreColor(match.match_score)}`}>
                        {match.match_score.toFixed(0)}%
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">Match Score</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No matches yet</h3>
            <p className="text-muted-foreground text-center">
              Create matches by matching your resumes with job descriptions
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
