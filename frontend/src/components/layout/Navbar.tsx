import { Link, useLocation } from 'react-router-dom';
import { FileText, MessageSquare, LayoutDashboard, User2, Sun, Moon, X } from 'lucide-react';
import { Button } from '../ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { getInitials } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface NavbarProps {
  isOpen: boolean;
  isDesktop: boolean;
  onClose: () => void;
}

export default function Navbar({ isOpen, isDesktop, onClose }: NavbarProps) {
  const location = useLocation();
  const { user } = useAuthStore();
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' || 'dark';
    setTheme(savedTheme);
    document.documentElement.classList.toggle('light', savedTheme === 'light');
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('light', newTheme === 'light');
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/files', icon: FileText, label: 'Files Studio' },
    { path: '/chat', icon: MessageSquare, label: 'Chat' },
    { path: '/profile', icon: User2, label: 'Profile' },
  ];

  return (
    <div className='block'>
      {/* Mobile overlay - only on medium and small screens */}
      {isOpen && !isDesktop && (
        <div
          className="fixed inset-0 z-40 bg-background/80 border border-red backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Navbar */}
      <nav
        className={cn(
          "z-50 bg-card transition-transform duration-300",
          // Mobile/tablet: slide in from right
          "fixed top-0 right-0 h-screen w-64 flex flex-col border-l lg:hidden",
          isOpen ? "translate-x-0" : "translate-x-full",
          // Desktop: fixed on left, always visible
          "lg:fixed lg:top-0 lg:left-0 lg:flex lg:w-full lg:px-20 lg:box-border lg:h-16 lg:justify-center lg:translate-x-0 lg:flex-row lg:border-b lg:border-r-0"
        )}
      >
        {/* Header + Nav wrapper */}
        <div className="flex h-full flex-col lg:h-full lg:box-border lg:w-full lg:h-16 lg:flex-row lg:justify-between lg:px-6">

        {/* LEFT: Logo */}
        <div className="flex items-center justify-between border-b p-4 lg:border-0 lg:p-0">
          <Link to="/" className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <FileText className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-brand to-secondary bg-clip-text text-transparent">Inkris</span>
          </Link>

          {/* Mobile Close */}
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onClose}
          >
            <X className="h-5 w-5 text-destructive" />
          </Button>
        </div>

        {/* CENTER: Navigation */}
        <div className="flex-1 space-y-1 overflow-y-auto p-4 lg:flex lg:items-center lg:justify-center lg:space-y-0 lg:space-x-6 lg:overflow-visible lg:px-6 lg:py-0">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);

            return (
              <Link key={item.path} to={item.path} onClick={onClose} className='lg:h-full'>
                <div
                  className={cn(
                    "flex items-center space-x-3 rounded-lg px-3 py-2 transition-colors",
                    "lg:space-x-2 lg:px-2 lg:my-0 lg:h-full lg:w-full lg:rounded-[0]",
                    isActive
                      ? (isDesktop ? "border-b-2 border-primary text-primary":"bg-primary text-primary-foreground")
                      : "hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.label}</span>
                </div>
              </Link>
            );
          })}
        </div>

        {/* RIGHT: Theme + User */}
        <div className="border-t p-4 space-y-4 lg:border-0 lg:p-0 lg:space-y-0 lg:flex lg:items-center lg:space-x-4">

          {/* Theme Toggle */}
          <div className="flex items-center justify-between lg:justify-center lg:space-x-2">
            <span className="text-sm text-muted-foreground lg:hidden">
              Theme
            </span>
            <Button variant="ghost" size="icon" onClick={toggleTheme}>
              {theme === "dark" ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>
          </div>

          {/* User */}
          {user && (
            <div className="flex items-center space-x-3 rounded-lg bg-muted p-3 lg:bg-transparent lg:p-0">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground font-semibold text-sm">
                {getInitials(user.first_name, user.last_name)}
              </div>

              <div className="flex-1 min-w-0 lg:hidden">
                <p className="text-sm font-medium truncate">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user.email}
                </p>
              </div>
            </div>
          )}
        </div>
        </div>
      </nav>
    </div>
  );
}