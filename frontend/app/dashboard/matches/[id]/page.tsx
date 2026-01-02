'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft, CheckCircle2, XCircle, Lightbulb, TrendingUp, Wand2, Copy, Check,
  Download, FileText, FileDown, Sparkles, Target, AlertTriangle, RefreshCw
} from 'lucide-react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useMatch } from '@/lib/hooks/useMatches';
import { resumesAPI, RewriteResponse } from '@/lib/api/resumes';
import { matchesAPI, InterviewPrepResponse, CoverLetterResponse } from '@/lib/api/matches';
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
  const [downloadingImprovedResume, setDownloadingImprovedResume] = useState(false);
  const [savingImprovedResume, setSavingImprovedResume] = useState(false);
  const [rescanningResume, setRescanningResume] = useState(false);

  // Interview Prep
  const [interviewPrep, setInterviewPrep] = useState<InterviewPrepResponse | null>(null);
  const [generatingInterview, setGeneratingInterview] = useState(false);
  const [downloadingInterview, setDownloadingInterview] = useState(false);

  // Cover Letter
  const [coverLetter, setCoverLetter] = useState<CoverLetterResponse | null>(null);
  const [generatingCoverLetter, setGeneratingCoverLetter] = useState(false);
  const [downloadingCoverLetter, setDownloadingCoverLetter] = useState(false);
  const [coverLetterTone, setCoverLetterTone] = useState<'professional' | 'enthusiastic' | 'formal'>('professional');

  // Load cached data when match loads
  useEffect(() => {
    if (match) {
      // Load cached interview prep
      if (match.interview_prep_data) {
        setInterviewPrep(match.interview_prep_data as InterviewPrepResponse);
      }

      // Load cached cover letter
      if (match.cover_letter_data) {
        setCoverLetter(match.cover_letter_data as CoverLetterResponse);
        // Set tone from cached data
        const cachedTone = match.cover_letter_data.tone as 'professional' | 'enthusiastic' | 'formal';
        if (cachedTone) {
          setCoverLetterTone(cachedTone);
        }
      }

      // Load cached improved resume
      if (match.improved_resume_data) {
        setRewriteResult(match.improved_resume_data as RewriteResponse);
      }
    }
  }, [match]);

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

  // Interview Prep handlers
  const generateInterviewPrep = async () => {
    setGeneratingInterview(true);
    try {
      const result = await matchesAPI.generateInterviewPrep(id);
      setInterviewPrep(result.data);
      toast.success('Interview questions generated!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate interview prep');
    } finally {
      setGeneratingInterview(false);
    }
  };

  const downloadInterviewPrep = async (format: 'docx' | 'pdf') => {
    setDownloadingInterview(true);
    try {
      const response = format === 'docx'
        ? await matchesAPI.downloadInterviewDocx(id)
        : await matchesAPI.downloadInterviewPdf(id);

      const blob = new Blob([response.data], {
        type: format === 'docx'
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `interview-prep-${id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(`Downloaded interview prep as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download');
    } finally {
      setDownloadingInterview(false);
    }
  };

  // Cover Letter handlers
  const generateCoverLetter = async () => {
    setGeneratingCoverLetter(true);
    try {
      const result = await matchesAPI.generateCoverLetter(id, { tone: coverLetterTone });
      setCoverLetter(result.data);
      toast.success('Cover letter generated!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate cover letter');
    } finally {
      setGeneratingCoverLetter(false);
    }
  };

  const downloadCoverLetter = async () => {
    setDownloadingCoverLetter(true);
    try {
      const response = await matchesAPI.downloadCoverLetterDocx(id, coverLetterTone);
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cover-letter-${id}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Downloaded cover letter as DOCX');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download');
    } finally {
      setDownloadingCoverLetter(false);
    }
  };

  const downloadCoverLetterPdf = async () => {
    setDownloadingCoverLetter(true);
    try {
      const response = await matchesAPI.downloadCoverLetterPdf(id, coverLetterTone);
      const blob = new Blob([response.data], {
        type: 'application/pdf'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cover-letter-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Downloaded cover letter as PDF');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download');
    } finally {
      setDownloadingCoverLetter(false);
    }
  };

  // Resume download handlers
  const downloadResume = async (format: 'docx' | 'pdf') => {
    if (!match) return;
    try {
      const response = format === 'docx'
        ? await resumesAPI.downloadDocx(match.resume_id)
        : await resumesAPI.downloadPdf(match.resume_id);

      const blob = new Blob([response.data], {
        type: format === 'docx'
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resume-${match.resume_id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(`Downloaded resume as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download');
    }
  };

  // Improved resume handlers
  const downloadImprovedResume = async (format: 'docx' | 'pdf') => {
    setDownloadingImprovedResume(true);
    try {
      const response = await resumesAPI.downloadImprovedResume(id, format);
      const blob = new Blob([response.data], {
        type: format === 'docx'
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `improved-resume-${id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(`Downloaded improved resume as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download');
    } finally {
      setDownloadingImprovedResume(false);
    }
  };

  const saveImprovedResume = async () => {
    setSavingImprovedResume(true);
    try {
      const response = await resumesAPI.saveImprovedResume(id);
      toast.success(response.data.message);
      toast.info('You can now use this improved resume for future job matches!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save resume');
    } finally {
      setSavingImprovedResume(false);
    }
  };

  const rescanImprovedResume = async (saveToCollection: boolean = false) => {
    setRescanningResume(true);
    try {
      const response = await resumesAPI.rescanImprovedResume(id, saveToCollection);
      toast.success(response.data.message);
      if (saveToCollection) {
        toast.info('Improved resume has been saved to your collection!');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to rescan resume');
    } finally {
      setRescanningResume(false);
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!match) {
    return <div>Match not found</div>;
  }

  const matchData = [{ value: match.match_score }];
  const matchFill = match.match_score >= 80 ? '#10b981' : match.match_score >= 60 ? '#f59e0b' : '#ef4444';

  const atsData = match.ats_score ? [{ value: match.ats_score }] : null;
  const atsFill = match.ats_score && match.ats_score >= 80 ? '#10b981' : match.ats_score && match.ats_score >= 60 ? '#f59e0b' : '#ef4444';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        <div className="flex gap-2">
          <Button onClick={() => downloadResume('docx')} variant="outline" size="sm">
            <FileText className="h-4 w-4 mr-2" />
            Resume DOCX
          </Button>
          <Button onClick={() => downloadResume('pdf')} variant="outline" size="sm">
            <FileDown className="h-4 w-4 mr-2" />
            Resume PDF
          </Button>
        </div>
      </div>

      {/* Match & ATS Scores */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Match Score Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Match Score
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <div className="relative w-full max-w-xs aspect-square">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius="60%"
                  outerRadius="90%"
                  data={matchData}
                  startAngle={90}
                  endAngle={-270}
                >
                  <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                  <RadialBar dataKey="value" cornerRadius={10} fill={matchFill} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-5xl font-bold" style={{ color: matchFill }}>
                  {match.match_score.toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground mt-1">Job Fit</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ATS Score Card */}
        {match.ats_score !== null && atsData && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                ATS Score
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <div className="relative w-full max-w-xs aspect-square">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    cx="50%"
                    cy="50%"
                    innerRadius="60%"
                    outerRadius="90%"
                    data={atsData}
                    startAngle={90}
                    endAngle={-270}
                  >
                    <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                    <RadialBar dataKey="value" cornerRadius={10} fill={atsFill} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-5xl font-bold" style={{ color: atsFill }}>
                    {match.ats_score.toFixed(0)}%
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">ATS Compatible</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Keyword Matches */}
      {match.keyword_matches && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Keyword Analysis
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {match.keyword_matches.match_percentage}% keyword match rate
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {match.keyword_matches.matched && match.keyword_matches.matched.length > 0 && (
              <div>
                <h4 className="font-medium mb-2 text-sm">Matched Keywords:</h4>
                <div className="flex flex-wrap gap-2">
                  {match.keyword_matches.matched.map((keyword, idx) => (
                    <Badge key={idx} variant="default" className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {match.keyword_matches.missing && match.keyword_matches.missing.length > 0 && (
              <div>
                <h4 className="font-medium mb-2 text-sm">Missing Keywords:</h4>
                <div className="flex flex-wrap gap-2">
                  {match.keyword_matches.missing.map((keyword, idx) => (
                    <Badge key={idx} variant="outline" className="border-orange-500 text-orange-700 dark:text-orange-400">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ATS Issues */}
      {match.ats_issues && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              ATS Compatibility Issues
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {match.ats_issues.formatting_issues && Array.isArray(match.ats_issues.formatting_issues) && match.ats_issues.formatting_issues.length > 0 && (
              <div>
                <h4 className="font-medium mb-2 text-sm">Formatting Issues:</h4>
                <ul className="space-y-1 text-sm">
                  {match.ats_issues.formatting_issues.map((issue, idx) => (
                    <li key={idx} className="flex gap-2">
                      <span className="text-orange-500">•</span>
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {match.ats_issues.missing_sections && Array.isArray(match.ats_issues.missing_sections) && match.ats_issues.missing_sections.length > 0 && (
              <div>
                <h4 className="font-medium mb-2 text-sm">Missing Sections:</h4>
                <ul className="space-y-1 text-sm">
                  {match.ats_issues.missing_sections.map((section, idx) => (
                    <li key={idx} className="flex gap-2">
                      <span className="text-red-500">•</span>
                      <span>{section}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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

      {/* Interview Prep Section */}
      <Card className="border-blue-500/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-500" />
                Interview Preparation
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-2">
                AI-generated interview questions tailored to this job
              </p>
            </div>
            {!interviewPrep ? (
              <Button
                onClick={generateInterviewPrep}
                disabled={generatingInterview}
                variant="outline"
                className="border-blue-500 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                {generatingInterview ? 'Generating...' : 'Generate Questions'}
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button
                  onClick={() => downloadInterviewPrep('docx')}
                  disabled={downloadingInterview}
                  variant="outline"
                  size="sm"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  DOCX
                </Button>
                <Button
                  onClick={() => downloadInterviewPrep('pdf')}
                  disabled={downloadingInterview}
                  variant="outline"
                  size="sm"
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  PDF
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        {interviewPrep && (
          <CardContent className="space-y-6">
            {interviewPrep.technical_questions && Array.isArray(interviewPrep.technical_questions) && interviewPrep.technical_questions.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Technical Questions:</h4>
                <div className="space-y-3">
                  {interviewPrep.technical_questions.map((q, idx) => (
                    <div key={idx} className="border rounded-lg p-3">
                      <p className="font-medium text-sm mb-2">{q.question}</p>
                      <p className="text-sm text-muted-foreground">{q.suggested_answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {interviewPrep.behavioral_questions && Array.isArray(interviewPrep.behavioral_questions) && interviewPrep.behavioral_questions.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Behavioral Questions:</h4>
                <div className="space-y-3">
                  {interviewPrep.behavioral_questions.map((q, idx) => (
                    <div key={idx} className="border rounded-lg p-3">
                      <p className="font-medium text-sm mb-2">{q.question}</p>
                      <p className="text-sm text-muted-foreground">{q.star_example}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {interviewPrep.talking_points && Array.isArray(interviewPrep.talking_points) && interviewPrep.talking_points.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Key Talking Points:</h4>
                <ul className="space-y-1 text-sm">
                  {interviewPrep.talking_points.map((point, idx) => (
                    <li key={idx} className="flex gap-2">
                      <span className="text-blue-500">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Cover Letter Section */}
      <Card className="border-purple-500/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-purple-500" />
                Cover Letter Generator
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-2">
                AI-generated cover letter for this position
              </p>
            </div>
            <div className="flex gap-2 items-center">
              {!coverLetter && (
                <select
                  value={coverLetterTone}
                  onChange={(e) => setCoverLetterTone(e.target.value as any)}
                  className="px-3 py-1.5 border border-input bg-background rounded-md text-sm"
                >
                  <option value="professional">Professional</option>
                  <option value="enthusiastic">Enthusiastic</option>
                  <option value="formal">Formal</option>
                </select>
              )}
              {!coverLetter ? (
                <Button
                  onClick={generateCoverLetter}
                  disabled={generatingCoverLetter}
                  variant="outline"
                  className="border-purple-500 text-purple-500 hover:bg-purple-50 dark:hover:bg-purple-950"
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  {generatingCoverLetter ? 'Generating...' : 'Generate Letter'}
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button
                    onClick={downloadCoverLetter}
                    disabled={downloadingCoverLetter}
                    variant="outline"
                    size="sm"
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    DOCX
                  </Button>
                  <Button
                    onClick={() => downloadCoverLetterPdf()}
                    disabled={downloadingCoverLetter}
                    variant="outline"
                    size="sm"
                  >
                    <FileDown className="h-4 w-4 mr-2" />
                    PDF
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        {coverLetter && (
          <CardContent>
            <div className="bg-muted/50 p-6 rounded-lg">
              <pre className="whitespace-pre-wrap font-sans text-sm">{coverLetter.cover_letter}</pre>
            </div>
          </CardContent>
        )}
      </Card>

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
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => downloadImprovedResume('docx')}
                  disabled={downloadingImprovedResume}
                  variant="outline"
                  size="sm"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  DOCX
                </Button>
                <Button
                  onClick={() => downloadImprovedResume('pdf')}
                  disabled={downloadingImprovedResume}
                  variant="outline"
                  size="sm"
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  PDF
                </Button>
                <Button
                  onClick={() => rescanImprovedResume(false)}
                  disabled={rescanningResume}
                  variant="outline"
                  size="sm"
                  className="border-blue-500 text-blue-500"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {rescanningResume ? 'Rescanning...' : 'Rescan'}
                </Button>
                <Button
                  onClick={saveImprovedResume}
                  disabled={savingImprovedResume}
                  variant="default"
                  size="sm"
                >
                  <Download className="h-4 w-4 mr-2" />
                  {savingImprovedResume ? 'Saving...' : 'Save to Resumes'}
                </Button>
                <Button onClick={handleCopy} variant="outline" size="sm">
                  {copied ? <Check className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {rewriteResult.key_improvements && Array.isArray(rewriteResult.key_improvements) && rewriteResult.key_improvements.length > 0 && (
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

            <div>
              <h3 className="font-semibold mb-3">Improved Resume:</h3>
              <div className="bg-muted/50 p-6 rounded-lg">
                <pre className="whitespace-pre-wrap font-sans text-sm">{rewriteResult.improved_resume}</pre>
              </div>
            </div>

            {rewriteResult.changes_summary && Array.isArray(rewriteResult.changes_summary) && rewriteResult.changes_summary.length > 0 && (
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

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Match Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Created</p>
              <p className="font-medium">{formatDate(match.created_at)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Match ID</p>
              <p className="font-medium">#{match.id}</p>
            </div>
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
    </div>
  );
}
