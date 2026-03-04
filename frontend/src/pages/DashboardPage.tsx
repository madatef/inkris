import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore } from '@/stores/auth-store';
import { useQuotaStore } from '@/stores/quota-store';
import { FileText, MessageSquare, Settings, Upload, Database, Search, Image, Video, Zap, FileStack } from 'lucide-react';
import { formatBytes, formatNumber } from '@/lib/utils';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { quotas, fetchQuotas, getWarnings } = useQuotaStore();

  useEffect(() => {
    fetchQuotas();
  }, [fetchQuotas]);

  const quickActions = [
    { icon: Upload, label: 'Upload Files', description: 'Add new documents to your library', to: '/files' },
    { icon: MessageSquare, label: 'Start Chatting', description: 'Create a new conversation', to: '/chat' },
    { icon: Settings, label: 'View Settings', description: 'Manage your profile and preferences', to: '/settings' },
  ];

  const quotaCards = quotas ? [
    { icon: FileText, label: 'Files Remaining', value: quotas.files, color: 'bg-blue-500' },
    { icon: Database, label: 'Storage Remaining', value: formatBytes(quotas.storage_bytes), color: 'bg-purple-500' },
    { icon: MessageSquare, label: 'Conversations Remaining', value: quotas.conversations, color: 'bg-green-500' },
    { icon: Zap, label: 'LLM Tokens Remaining', value: formatNumber(quotas.llm_tokens), color: 'bg-orange-500' },
    { icon: Search, label: 'Web Searches Remaining', value: quotas.web_searches, color: 'bg-cyan-500' },
    { icon: Image, label: 'Image Generations Remaining', value: quotas.image_generations, color: 'bg-pink-500' },
    { icon: Video, label: 'Video Generations Remaining', value: quotas.video_generations, color: 'bg-red-500' },
    { icon: FileStack, label: 'File Processing Remaining', value: quotas.file_processing, color: 'bg-yellow-500' },
  ] : [];

  const warnings = getWarnings();

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="container mx-auto max-w-6xl space-y-8 p-8">
        {/* Welcome Header */}
        <div>
          <h1 className="text-4xl font-bold">Welcome back, <span className='bg-gradient-to-r from-brand to-secondary bg-clip-text text-transparent'>{user?.first_name}!</span></h1>
          <p className="mt-2 text-muted-foreground">
            Here's an overview of your Inkris usage and quota status
          </p>
        </div>

        {/* Warnings */}
        {warnings.length > 0 && (
          <Card className="border-yellow-500 bg-yellow-500/10">
            <CardHeader>
              <CardTitle className="text-yellow-600 dark:text-yellow-400">⚠️ Quota Warnings</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1">
                {warnings.map((warning, index) => (
                  <li key={index} className="text-sm">{warning}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <div>
          <h2 className="mb-4 text-2xl font-semibold">Quick Actions</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {quickActions.map((action, index) => {
              const Icon = action.icon;
              return (
                <Link key={index} to={action.to}>
                  <Card className="cursor-pointer transition-all hover:border-primary hover:shadow-md">
                    <CardHeader>
                      <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                        <Icon className="h-6 w-6" />
                      </div>
                      <CardTitle>{action.label}</CardTitle>
                      <CardDescription>{action.description}</CardDescription>
                    </CardHeader>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Quota Status */}
        <div>
          <h2 className="mb-4 text-2xl font-semibold">Quota Status</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {quotaCards.map((quota, index) => {
              const Icon = quota.icon;
              return (
                <Card key={index}>
                  <CardHeader className="pb-3">
                    <div className={`mb-2 flex h-10 w-10 items-center justify-center rounded-lg ${quota.color} text-white`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-3xl font-bold">{quota.value}</CardTitle>
                    <CardDescription>{quota.label}</CardDescription>
                  </CardHeader>
                </Card>
              );
            })}
          </div>

          <Card className="mt-4">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">
                <strong className='text-primary'>Note:</strong> These values represent your remaining quota, not usage. When any quota reaches zero,
                the corresponding action will be blocked. Please contact the developer if you need to increase your limits.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}