'use client';

import { useState } from 'react';
import Link from 'next/link';
import { MessageSquare, X } from 'lucide-react';
import { toast } from 'sonner';

export default function LandingPage() {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackForm, setFeedbackForm] = useState({ name: '', email: '', message: '' });
  const [submitting, setSubmitting] = useState(false);

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackForm),
      });

      if (response.ok) {
        toast.success('Thank you for your feedback!');
        setShowFeedback(false);
        setFeedbackForm({ name: '', email: '', message: '' });
      } else {
        toast.error('Failed to submit feedback');
      }
    } catch (error) {
      toast.error('Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col relative">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-heading font-bold">CareerAlign.ai</h1>
          <div className="flex gap-4">
            <Link
              href="/login"
              className="px-4 py-2 text-sm font-medium hover:underline"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="container mx-auto px-4 py-24 text-center">
          <h2 className="text-5xl md:text-6xl font-heading font-bold mb-6">
            AI-Powered Career Tools
          </h2>
          <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
            Match resumes to jobs, generate tailored cover letters, and prepare for interviews.
            Powered by multiple AI models (GPT-4, Claude, Gemini) for accurate analysis.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/register"
              className="px-8 py-3 text-lg font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
            >
              Start Matching
            </Link>
            <Link
              href="#features"
              className="px-8 py-3 text-lg font-medium border border-border rounded-lg hover:bg-accent transition"
            >
              Learn More
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="bg-card border-y border-border">
          <div className="container mx-auto px-4 py-20">
            <h3 className="text-3xl font-heading font-bold text-center mb-12">
              Key Features
            </h3>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="p-6 border border-border rounded-lg">
                <div className="text-4xl mb-4">📄</div>
                <h4 className="text-xl font-heading font-semibold mb-2">
                  Resume Analysis
                </h4>
                <p className="text-muted-foreground">
                  Upload your resume and get AI-powered extraction of skills, experience, and qualifications.
                </p>
              </div>

              <div className="p-6 border border-border rounded-lg">
                <div className="text-4xl mb-4">🎯</div>
                <h4 className="text-xl font-heading font-semibold mb-2">
                  Smart Matching
                </h4>
                <p className="text-muted-foreground">
                  Get detailed match scores with missing skills and personalized recommendations.
                </p>
              </div>

              <div className="p-6 border border-border rounded-lg">
                <div className="text-4xl mb-4">💼</div>
                <h4 className="text-xl font-heading font-semibold mb-2">
                  Cover Letters & Interview Prep
                </h4>
                <p className="text-muted-foreground">
                  Generate tailored cover letters and get AI-powered interview questions with suggested answers.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="container mx-auto px-4 py-20">
          <h3 className="text-3xl font-heading font-bold text-center mb-12">
            How It Works
          </h3>
          <div className="max-w-3xl mx-auto space-y-8">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-2">Upload Your Resume</h4>
                <p className="text-muted-foreground">
                  Upload your resume in PDF, DOCX, or TXT format. Our AI will analyze and extract your skills.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-2">Add Job Descriptions</h4>
                <p className="text-muted-foreground">
                  Paste job descriptions or LinkedIn URLs for positions you&apos;re interested in.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-2">Get Comprehensive Results</h4>
                <p className="text-muted-foreground">
                  Receive match scores, AI-optimized resumes, personalized cover letters, and interview prep questions.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="container mx-auto px-4 py-8 text-center text-muted-foreground">
          <p>&copy; 2025 CareerAlign.ai</p>
        </div>
      </footer>

      {/* Feedback Button */}
      <button
        onClick={() => setShowFeedback(true)}
        className="fixed bottom-6 right-6 bg-primary text-primary-foreground p-4 rounded-full shadow-lg hover:bg-primary/90 transition-all z-50"
        aria-label="Send Feedback"
      >
        <MessageSquare className="h-6 w-6" />
      </button>

      {/* Feedback Modal */}
      {showFeedback && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-card border border-border rounded-lg p-6 max-w-md w-full relative">
            <button
              onClick={() => setShowFeedback(false)}
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </button>

            <h2 className="text-2xl font-heading font-bold mb-4">Send Feedback</h2>
            <p className="text-sm text-muted-foreground mb-6">
              We'd love to hear from you! Share your thoughts, suggestions, or report issues.
            </p>

            <form onSubmit={handleFeedbackSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-2">
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  required
                  value={feedbackForm.name}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Your name"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-2">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={feedbackForm.email}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, email: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="your@email.com"
                />
              </div>

              <div>
                <label htmlFor="message" className="block text-sm font-medium mb-2">
                  Message
                </label>
                <textarea
                  id="message"
                  required
                  rows={5}
                  value={feedbackForm.message}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, message: e.target.value })}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                  placeholder="Tell us what you think..."
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowFeedback(false)}
                  className="flex-1 px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 font-medium"
                >
                  {submitting ? 'Sending...' : 'Send Feedback'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
