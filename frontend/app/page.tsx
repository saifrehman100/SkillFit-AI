import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
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
            AI-Powered Resume Matching
          </h2>
          <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
            Get instant insights on how well your resume matches job descriptions.
            Powered by advanced AI models for accurate skill analysis.
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
                  LinkedIn Integration
                </h4>
                <p className="text-muted-foreground">
                  Scan LinkedIn job postings and instantly see how well you match.
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
                <h4 className="text-xl font-semibold mb-2">Get Instant Results</h4>
                <p className="text-muted-foreground">
                  Receive detailed match scores, missing skills analysis, and recommendations to improve your chances.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="container mx-auto px-4 py-8 text-center text-muted-foreground">
          <p>&copy; 2025 CareerAlign.ai. Powered by advanced AI models.</p>
        </div>
      </footer>
    </div>
  );
}
