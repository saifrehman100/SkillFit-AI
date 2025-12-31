'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, CheckCircle2, XCircle } from 'lucide-react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useMatch } from '@/lib/hooks/useMatches';
import { formatDate } from '@/lib/utils';

export default function MatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt(params.id as string);
  const { match, isLoading } = useMatch(id);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!match) {
    return <div>Match not found</div>;
  }

  const data = [{ value: match.match_score }];
  const fill = match.match_score >= 80 ? '#10b981' : match.match_score >= 60 ? '#f59e0b' : '#ef4444';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>

      {/* Match Score Card */}
      <Card>
        <CardHeader>
          <CardTitle>Match Result #{match.id}</CardTitle>
          <p className="text-sm text-muted-foreground">
            Created {formatDate(match.created_at)}
          </p>
        </CardHeader>
        <CardContent className="flex flex-col items-center">
          {/* Score Gauge */}
          <div className="relative w-full max-w-sm aspect-square">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart
                cx="50%"
                cy="50%"
                innerRadius="60%"
                outerRadius="90%"
                data={data}
                startAngle={90}
                endAngle={-270}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar
                  dataKey="value"
                  cornerRadius={10}
                  fill={fill}
                />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-6xl font-bold" style={{ color: fill }}>
                {match.match_score.toFixed(0)}%
              </div>
              <div className="text-lg text-muted-foreground mt-2">Match Score</div>
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 w-full mt-8 text-sm">
            <div>
              <p className="text-muted-foreground">Resume ID</p>
              <p className="font-medium">#{match.resume_id}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Job ID</p>
              <p className="font-medium">#{match.job_id}</p>
            </div>
            {match.llm_provider && (
              <div>
                <p className="text-muted-foreground">AI Provider</p>
                <p className="font-medium">{match.llm_provider}</p>
              </div>
            )}
            {match.llm_model && (
              <div>
                <p className="text-muted-foreground">Model</p>
                <p className="font-medium text-xs">{match.llm_model}</p>
              </div>
            )}
            {match.tokens_used && (
              <div>
                <p className="text-muted-foreground">Tokens Used</p>
                <p className="font-medium">{match.tokens_used.toLocaleString()}</p>
              </div>
            )}
            {match.cost_estimate && (
              <div>
                <p className="text-muted-foreground">Est. Cost</p>
                <p className="font-medium">${match.cost_estimate.toFixed(4)}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Missing Skills */}
      {match.missing_skills && match.missing_skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-red-500" />
              Missing Skills
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {match.missing_skills.map((skill, idx) => (
                <Badge key={idx} variant="destructive">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {match.recommendations && match.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {match.recommendations.map((rec, idx) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-muted-foreground">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Explanation */}
      {match.explanation && (
        <Card>
          <CardHeader>
            <CardTitle>Detailed Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap">{match.explanation}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
