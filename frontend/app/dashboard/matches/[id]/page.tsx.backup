'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, CheckCircle2, XCircle, Lightbulb, TrendingUp, Wand2, Copy, Check } from 'lucide-react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useMatch } from '@/lib/hooks/useMatches';
import { resumesAPI, RewriteResponse } from '@/lib/api/resumes';
import { formatDate } from '@/lib/utils';
import { toast } from 'sonner';

export default function MatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt(params.id as string);
  const { match, isLoading } = useMatch(id);
  const [rewriting, setRewriting] = useState(false);
  const [rewriteResult, setRewriteResult] = useState<RewriteResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleRewrite = async () => {
    if (!match) return;

    setRewriting(true);
    try {
      const result = await resumesAPI.rewrite(match.resume_id, match.job_id, match.id);
      setRewriteResult(result.data);
      toast.success('Resume improved successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to rewrite resume');
    } finally {
      setRewriting(false);
    }
  };

  const handleCopy = () => {
    if (rewriteResult?.improved_resume) {
      navigator.clipboard.writeText(rewriteResult.improved_resume);
      setCopied(true);
      toast.success('Copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

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
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-yellow-500" />
                  AI-Powered Recommendations
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-2">
                  Actionable steps to improve your match score
                </p>
              </div>
              <Button
                onClick={handleRewrite}
                disabled={rewriting}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                <Wand2 className="h-4 w-4 mr-2" />
                {rewriting ? 'Generating...' : 'Rewrite Resume'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {match.recommendations.map((rec: any, idx: number) => {
                // Handle both old format (string) and new format (object)
                const isStructured = typeof rec === 'object' && rec.action;
                const priorityColors = {
                  High: 'bg-red-500/10 text-red-500 border-red-500/20',
                  Medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
                  Low: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
                };

                return (
                  <div
                    key={idx}
                    className="border rounded-lg p-4 space-y-3 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="font-medium">
                          {isStructured ? rec.action : rec}
                        </p>
                        {isStructured && rec.reason && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {rec.reason}
                          </p>
                        )}
                      </div>
                      {isStructured && (
                        <div className="flex gap-2 shrink-0">
                          {rec.priority && (
                            <Badge
                              variant="outline"
                              className={priorityColors[rec.priority as keyof typeof priorityColors]}
                            >
                              {rec.priority}
                            </Badge>
                          )}
                          {rec.impact_estimate && (
                            <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                              <TrendingUp className="h-3 w-3 mr-1" />
                              +{rec.impact_estimate}%
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Improved Resume */}
      {rewriteResult && (
        <Card className="border-primary">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Wand2 className="h-5 w-5 text-primary" />
                  AI-Improved Resume
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-2">
                  Estimated new score: {rewriteResult.estimated_new_score}%
                  <span className="text-green-500 ml-2">
                    (+{rewriteResult.score_improvement} points)
                  </span>
                </p>
              </div>
              <Button onClick={handleCopy} variant="outline">
                {copied ? <Check className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Key Improvements */}
            {rewriteResult.key_improvements && rewriteResult.key_improvements.length > 0 && (
              <div>
                <h3 className="font-semibold mb-3">Key Improvements:</h3>
                <ul className="space-y-2">
                  {rewriteResult.key_improvements.map((improvement, idx) => (
                    <li key={idx} className="flex gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                      <span>{improvement}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Improved Resume Text */}
            <div>
              <h3 className="font-semibold mb-3">Improved Resume:</h3>
              <div className="bg-muted/50 p-6 rounded-lg">
                <pre className="whitespace-pre-wrap font-sans text-sm">{rewriteResult.improved_resume}</pre>
              </div>
            </div>

            {/* Changes Summary */}
            {rewriteResult.changes_summary && rewriteResult.changes_summary.length > 0 && (
              <div>
                <h3 className="font-semibold mb-3">Changes Made:</h3>
                <ul className="space-y-1">
                  {rewriteResult.changes_summary.map((change, idx) => (
                    <li key={idx} className="flex gap-2 text-sm text-muted-foreground">
                      <span>•</span>
                      <span>{change}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
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
