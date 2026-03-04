import { useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import {LogOut} from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import { useQuotaStore } from '@/stores/quota-store';
import { formatBytes, formatDate, formatNumber } from '@/lib/utils';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';
import { useState } from 'react';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { quotas, fetchQuotas, isLoading } = useQuotaStore();
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    fetchQuotas();
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' || 'dark';
    setTheme(savedTheme);
  }, [fetchQuotas]);

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  const toggleTheme = (checked: boolean) => {
    const newTheme = checked ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('light', newTheme === 'light');
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="container mx-auto max-w-4xl space-y-8 p-8">
        <div>
          <h1 className="text-4xl font-bold">Profile</h1>
          <p className="mt-2 text-muted-foreground">Manage your profile and preferences</p>
        </div>

        {/* Profile Section */}
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-sm font-medium text-muted-foreground">First Name</p>
                <p className="text-lg font-medium">{user?.first_name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Last Name</p>
                <p className="text-lg font-medium">{user?.last_name}</p>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Email Address</p>
              <p className="text-lg font-medium">{user?.email}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Member Since</p>
              <p className="text-lg font-medium">
                {user?.created_at ? formatDate(user.created_at) : '-'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Appearance Section */}
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Customize how Inkris looks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Theme</p>
                <p className="text-sm text-muted-foreground">Switch between light and dark mode</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm">Light</span>
                <Switch checked={theme === 'dark'} onCheckedChange={toggleTheme} />
                <span className="text-sm">Dark</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Usage Statistics */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Statistics</CardTitle>
            <CardDescription>Your remaining quotas</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : quotas ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Files Remaining</p>
                  <p className="text-2xl font-bold">{quotas.files}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Storage Remaining</p>
                  <p className="text-2xl font-bold">{formatBytes(quotas.storage_bytes)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Conversations Remaining</p>
                  <p className="text-2xl font-bold">{quotas.conversations}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">LLM Tokens Remaining</p>
                  <p className="text-2xl font-bold">{formatNumber(quotas.llm_tokens)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Web Searches</p>
                  <p className="text-2xl font-bold">{quotas.web_searches}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Image Generations</p>
                  <p className="text-2xl font-bold">{quotas.image_generations}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Video Generations</p>
                  <p className="text-2xl font-bold">{quotas.video_generations}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">File Processing</p>
                  <p className="text-2xl font-bold">{quotas.file_processing}</p>
                </div>
              </div>
            ) : null}
            <p className="mt-4 text-sm text-muted-foreground">
              <strong>Note:</strong> All values shown are remaining quota, not usage. Contact the developer if you need
              to increase your limits.
            </p>
          </CardContent>
        </Card>

        {/* Account Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Account Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={handleLogout}>
              <LogOut className="w-5 h-5 mr-2" />
              Sign Out
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}