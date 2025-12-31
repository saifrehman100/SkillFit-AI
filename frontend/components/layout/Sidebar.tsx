'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, FileText, Briefcase, Target, Kanban, Settings, LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Resumes', href: '/dashboard/resumes', icon: FileText },
  { name: 'Jobs', href: '/dashboard/jobs', icon: Briefcase },
  { name: 'Matches', href: '/dashboard/matches', icon: Target },
  { name: 'Applications', href: '/dashboard/applications', icon: Kanban },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  return (
    <div className="flex flex-col h-full w-64 border-r border-border bg-card">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-heading font-bold">SkillFit AI</h1>
        <p className="text-sm text-muted-foreground mt-1">{user?.email}</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-border">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          <LogOut className="h-5 w-5" />
          Logout
        </button>
      </div>
    </div>
  );
}
