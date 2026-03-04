import { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { FileText, Image, Globe, Video, BarChart3, MessageSquare, Sparkles } from 'lucide-react';

export default function LandingPage() {
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const features = [
    {
      icon: MessageSquare,
      title: 'Intelligent Q&A',
      description: 'Get instant answers from your documents with advanced RAG technology',
    },
    {
      icon: Image,
      title: 'Image & Diagram Generation',
      description: 'Create visual representations and diagrams from your content',
    },
    {
      icon: FileText,
      title: 'Content Explanation',
      description: 'Understand complex topics with clear, detailed explanations',
    },
    {
      icon: Globe,
      title: 'Web Search & Scraping',
      description: 'Find similar content online and extract relevant information',
    },
    {
      icon: Video,
      title: 'Video Generation',
      description: 'Visualize scenes and concepts from your documents as videos',
    },
    {
      icon: BarChart3,
      title: 'Data Visualization',
      description: 'Generate plots and charts from tabular data automatically',
    },
  ];

  const handleFeedbackSubmit = async () => {
    if (!feedbackText.trim()) return;

    setIsSubmitting(true);
    try {
      await apiClient.post('/feedback', { text: feedbackText });
      setFeedbackText('');
      setFeedbackOpen(false);
      toast.success('Submitted. Thanks!')
    } catch (error) {
      toast.error('Failed to submit.')
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-muted/50">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link to="/" className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <FileText className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary/50 to-secondary bg-clip-text text-transparent">Inkris</span>
          </Link>
          <div className="flex items-center space-x-4">
            <Link to="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link to="/signup">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="inline-flex gap-2 border rounded-full px-4 py-2 text-sm font-medium text-bold">
          <Sparkles className="w-4 h-4" />
          <span className="text-sm font-semibold">AI-Powered File Assistant</span>
          </div>
          <h1 className="text-5xl font-bold leading-tight">
            Your Files, <br />
            <span className="bg-gradient-to-r from-primary/50 to-secondary bg-clip-text text-transparent">Supercharged with AI</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Upload your documents and unlock powerful AI capabilities: get instant answers, generate visuals,
            analyze data, explore related content across the web, and many more!
          </p>
          <div className="flex justify-center space-x-4">
            <Link to="/signup">
              <Button size="lg">Get Started (Free!)</Button>
            </Link>
            <a href="https://github.com/madatef/inkris" target="_blank" rel="noopener noreferrer">
              <Button size="lg" variant="outline" className='flex gap-4 px-4'>
                <svg xmlns="http://www.w3.org/2000/svg" fill="white" role="img" aria-hidden="true" className='w-5 h-5' viewBox="0 0 24 24">
                  <title>GitHub</title>
                  <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
                </svg>
                View on GitHub
              </Button>
            </a>
          </div>
          <p className="text-sm text-muted-foreground">
            Supports PDF, TXT, MD, XLS, XLSX • Up to 50MB per file
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-muted/50 py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold">Everything You Need</h2>
            <p className="mt-4 text-muted-foreground">
              Powerful AI features to transform how you work with files
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index}>
                  <CardHeader>
                    <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                      <Icon className="h-6 w-6" />
                    </div>
                    <CardTitle>{feature.title}</CardTitle>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardHeader>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 w-full">
        <div className="container mx-auto px-4 text-center w-full">
          <div className="mx-auto max-w-[90%] space-y-6">
            <h2 className="text-3xl font-bold">Ready to Transform Your Workflow?</h2>
            <p className="text-xl text-muted-foreground pb-4">
              Try Inkris now. It's totally free!<br /><br />
              <span className='text-sm'>If you feel like pushing the limits, visit our GitHub repo, fork, commit your changes, and submit a pull request. <br />If you think Inkris is useful, don't forget to star the repo ⭐!</span>
            </p>
            <div className='flex justify-center gap-4 w-full'>
              <Link to="/signup">
                <Button size="lg">Start Using Inkris</Button>
              </Link>
              <a href="https://github.com/madatef/inkris" target="_blank" rel="noopener noreferrer">
                <Button size="lg" variant="outline" className='flex gap-4 px-4'>
                  <svg xmlns="http://www.w3.org/2000/svg" fill="white" role="img" aria-hidden="true" className='w-5 h-5' viewBox="0 0 24 24">
                    <title>GitHub</title>
                    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
                  </svg>
                  GitHub repo
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 w-full">
        <div className="container mx-auto">
          <div className="flex flex-col justify-between items-center space-y-4 px-0 md:flex-row md:space-y-0 w-full">
            <div className="flex items-center justify-between space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <FileText className="h-5 w-5" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary/50 to-secondary bg-clip-text text-transparent">Inkris</span>
            </div>
            <div className="flex justify-between text-sm text-muted-foreground lg:ml-20">
              <Dialog open={feedbackOpen} onOpenChange={setFeedbackOpen}>
                <DialogTrigger asChild>
                  <Button variant="ghost">Send Feedback</Button>
                </DialogTrigger>
                <DialogContent className="w-[98vw] lg:max-w-[425px]">
                  <DialogHeader>
                    <DialogTitle>Send Feedback</DialogTitle>
                    <DialogDescription>
                      We'd love to hear your thoughts! Share your feedback with us.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <Textarea
                      placeholder="Type your feedback here..."
                      value={feedbackText}
                      onChange={(e) => setFeedbackText(e.target.value)}
                      className="min-h-[100px]"
                    />
                  </div>
                  <DialogFooter>
                    <Button
                      type="submit"
                      onClick={handleFeedbackSubmit}
                      disabled={!feedbackText.trim() || isSubmitting}
                    >
                      {isSubmitting ? 'Submitting...' : 'Submit'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              <a href="mailto:itsmadatef@gmail.com.com?subject=Inkris%20Contact%20Request" target='_blank'>
                <Button variant="ghost">Contact</Button>
              </a>
            </div>
            <p className="text-sm text-muted-foreground">© 2026 Inkris. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}