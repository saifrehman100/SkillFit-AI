# SkillFit AI - Frontend

Modern Next.js 14 frontend for SkillFit AI, an AI-powered resume-to-job matching platform with LinkedIn integration.

## Features

- **Authentication**: Secure JWT-based authentication with email/password
- **Resume Management**: Upload, parse, and manage resumes (PDF, DOCX, TXT)
- **Job Management**: Create and manage job postings with AI-powered skill extraction
- **Match Analysis**: AI-driven resume-to-job matching with visual score gauges
- **Application Tracking**: Kanban board for tracking job applications through the hiring pipeline
- **LinkedIn Scanner**: Public tool to scan LinkedIn job posts and match with resumes
- **Settings**: Manage API keys, LLM preferences, and account settings

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Data Fetching**: SWR (stale-while-revalidate)
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts
- **File Upload**: React Dropzone
- **Notifications**: Sonner
- **Icons**: Lucide React

## Prerequisites

- Node.js 20+ and npm
- Backend API running (see `/backend` folder)

## Getting Started

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env.local
   ```

3. **Configure environment variables:**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

5. **Open browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Docker Development

Run with hot reload:

```bash
# From project root
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend
```

### Docker Production

Build and run production build:

```bash
# From project root
docker-compose up --build frontend
```

## Project Structure

```
frontend/
├── app/                        # Next.js 14 App Router
│   ├── (auth)/                # Authentication pages
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/             # Protected dashboard pages
│   │   ├── applications/      # Job application tracker
│   │   ├── jobs/              # Job management
│   │   ├── matches/           # Match results
│   │   ├── resumes/           # Resume management
│   │   └── settings/          # User settings
│   ├── linkedin-scanner/      # Public LinkedIn scanner
│   ├── layout.tsx             # Root layout
│   └── page.tsx               # Landing page
├── components/
│   ├── layout/                # Sidebar, Header
│   └── ui/                    # shadcn/ui components
├── contexts/
│   └── AuthContext.tsx        # Global auth state
├── lib/
│   ├── api/                   # API client modules
│   ├── hooks/                 # Custom React hooks (SWR)
│   └── utils.ts               # Utility functions
├── types/
│   └── api.ts                 # TypeScript interfaces
├── Dockerfile                 # Production build
├── Dockerfile.dev             # Development build
└── next.config.js             # Next.js configuration
```

## Available Scripts

- `npm run dev` - Start development server on port 3000
- `npm run build` - Create production build
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |

## Key Features Implementation

### Authentication Flow

1. User registers/logs in
2. JWT token stored in localStorage
3. Axios interceptor adds `Authorization: Bearer <token>` to all requests
4. Protected routes redirect to `/login` if unauthenticated
5. User data fetched on mount via `AuthContext`

### File Upload

- Drag & drop interface using react-dropzone
- Supports PDF, DOCX, TXT (max 10MB)
- Progress indicator during upload
- Auto-refresh list after successful upload

### Match Visualization

- Recharts RadialBarChart for score gauge
- Color-coded scores:
  - Green (80-100): Excellent match
  - Amber (60-79): Good match
  - Red (0-59): Poor match
- Missing skills displayed as badges
- AI-generated recommendations

### Application Tracker

- Kanban board with 5 columns:
  - Wishlist
  - Applied
  - Interview
  - Offer
  - Rejected
- Simple status updates via dropdown
- Notes and URL tracking per application

## Design System

### Colors (Dark Mode)

- Background: `#0a0a0a`
- Card: `#141414`
- Primary: `#3b82f6` (blue)
- Success: `#10b981` (green)
- Warning: `#f59e0b` (amber)
- Danger: `#ef4444` (red)

### Typography

- Headings: **Space Grotesk** (700)
- Body: **Outfit** (400)
- Code: System monospace

### Component Patterns

- **Cards**: Dark background with subtle borders
- **Buttons**: Primary (filled), Secondary (outline), Ghost (text)
- **Forms**: Labels above inputs, inline error messages
- **Toasts**: Bottom-right corner notifications

## API Integration

All API calls use the `apiClient` from `/lib/api/client.ts`:

```typescript
import { apiClient } from '@/lib/api/client';

// Automatically adds Authorization header
const response = await apiClient.get('/resumes');
```

### Available API Modules

- `authAPI` - Login, register, getCurrentUser, regenerateAPIKey
- `resumesAPI` - Upload, list, get, delete
- `jobsAPI` - Create, list, get, update, delete
- `matchesAPI` - Create, list, get, delete
- `applicationsAPI` - Create, list, get, update, delete

### SWR Hooks

```typescript
import { useResumes } from '@/lib/hooks/useResumes';

function MyComponent() {
  const { resumes, isLoading, error, mutate } = useResumes();
  // ...
}
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 14+

## Performance Optimizations

- Server-side rendering (SSR) for public pages
- Client-side rendering (CSR) for dashboard (with auth)
- SWR caching for data fetching
- Image optimization via Next.js Image component
- Code splitting via dynamic imports
- Standalone output for minimal Docker images

## Security

- JWT tokens stored in localStorage (httpOnly cookies in production)
- CORS configured on backend
- Input validation with Zod schemas
- XSS protection via React's built-in escaping
- CSRF protection (future: use httpOnly cookies)

## Troubleshooting

### "Network Error" when calling API

- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS is enabled on backend

### Hot reload not working in Docker

- Use `docker-compose.dev.yml` for development
- Ensure volumes are mounted correctly

### Build fails with "Module not found"

- Run `npm install` to ensure all dependencies are installed
- Clear `.next` folder: `rm -rf .next`

## Contributing

1. Follow existing code structure
2. Use TypeScript for all new files
3. Add proper error handling and loading states
4. Test on mobile viewport
5. Run `npm run lint` before committing

## License

MIT

## Support

For issues and questions, open a GitHub issue in the main repository.
