/**
 * Onboarding tour configuration for first-time users
 * Using react-joyride to guide users through key features
 */

import { Step } from 'react-joyride';

export const dashboardTourSteps: Step[] = [
  {
    target: 'body',
    content: (
      <div>
        <h2 className="text-xl font-bold mb-2">Welcome to SkillFit AI! 🎉</h2>
        <p>Let's take a quick tour to help you get started. This will only take a minute!</p>
      </div>
    ),
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: '[data-tour="upload-resume"]',
    content: (
      <div>
        <h3 className="font-semibold mb-2">Upload Your Resume</h3>
        <p>Start by uploading your resume in PDF, DOCX, or TXT format. We'll analyze it and extract your skills, experience, and qualifications.</p>
      </div>
    ),
    placement: 'bottom',
  },
  {
    target: '[data-tour="add-job"]',
    content: (
      <div>
        <h3 className="font-semibold mb-2">Add Job Postings</h3>
        <p>Copy and paste job descriptions you're interested in. Our AI will analyze the requirements and keywords.</p>
      </div>
    ),
    placement: 'bottom',
  },
  {
    target: '[data-tour="create-match"]',
    content: (
      <div>
        <h3 className="font-semibold mb-2">Match Resume to Jobs</h3>
        <p>Once you have both a resume and job posting, create a match to see:</p>
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Match score (0-100%)</li>
          <li>ATS compatibility score</li>
          <li>Missing skills and keywords</li>
          <li>Personalized recommendations</li>
        </ul>
      </div>
    ),
    placement: 'bottom',
  },
  {
    target: '[data-tour="resumes-section"]',
    content: (
      <div>
        <h3 className="font-semibold mb-2">Your Resumes</h3>
        <p>All your uploaded resumes will appear here. You can view, edit, or delete them anytime.</p>
      </div>
    ),
    placement: 'top',
  },
  {
    target: '[data-tour="jobs-section"]',
    content: (
      <div>
        <h3 className="font-semibold mb-2">Your Job Postings</h3>
        <p>Track all the jobs you're interested in. Each job can be matched against multiple resumes.</p>
      </div>
    ),
    placement: 'top',
  },
  {
    target: '[data-tour="matches-section"]',
    content: (
      <div>
        <h3 className="font-semibold mb-2">Your Matches</h3>
        <p>View all your resume-job matches here. See scores, get AI-powered improvements, and generate cover letters!</p>
      </div>
    ),
    placement: 'top',
  },
  {
    target: '[data-tour="user-menu"]',
    content: (
      <div>
        <h3 className="font-semibold mb-2">Settings & Account</h3>
        <p>Access your API key, LLM preferences, usage statistics, and account settings from here.</p>
      </div>
    ),
    placement: 'bottom',
  },
  {
    target: 'body',
    content: (
      <div>
        <h2 className="text-xl font-bold mb-2">You're All Set! 🚀</h2>
        <p className="mb-2">You're ready to start optimizing your job applications with AI.</p>
        <p className="text-sm text-gray-600">Pro tip: Start by uploading a resume, then add a job you're interested in!</p>
      </div>
    ),
    placement: 'center',
  },
];

export const tourStyles = {
  options: {
    arrowColor: '#fff',
    backgroundColor: '#fff',
    overlayColor: 'rgba(0, 0, 0, 0.5)',
    primaryColor: '#3b82f6', // blue-500
    textColor: '#1f2937', // gray-800
    width: 380,
    zIndex: 10000,
  },
  buttonNext: {
    backgroundColor: '#3b82f6',
    borderRadius: '0.375rem',
    color: '#fff',
    fontSize: '0.875rem',
    padding: '0.5rem 1rem',
  },
  buttonBack: {
    color: '#6b7280',
    fontSize: '0.875rem',
    marginRight: '0.5rem',
  },
  buttonSkip: {
    color: '#6b7280',
    fontSize: '0.875rem',
  },
  tooltip: {
    borderRadius: '0.5rem',
    padding: '1.25rem',
  },
  tooltipContent: {
    padding: '0',
  },
};
