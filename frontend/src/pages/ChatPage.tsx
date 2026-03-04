import { useEffect, useRef, useState, } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowUp, Send, Loader2, Sidebar as SB, Plus , ChevronDown, Check} from 'lucide-react';
import * as Select from '@radix-ui/react-select'
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useChatStore } from '@/stores/chat-store';
import { useQuotaStore } from '@/stores/quota-store';
import { useFilesStore } from '@/stores/files-store';
import Sidebar from '@/components/layout/Sidebar';
import MessageList from '@/components/chat/MessageList';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Sparkles, FileText } from 'lucide-react';

export default function ChatPage() {
  const { id } = useParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    activeConversationId,
    setActiveConversation,
    fetchMessages,
    sendMessage,
    isStreaming,
    createConversation,
  } = useChatStore();

  const { canSendMessage, fetchQuotas, canCreateConversation } = useQuotaStore();
  const { files } = useFilesStore();

  // Conversation dialog state
  const [showNewConvoDialog, setShowNewConvoDialog] = useState(false);
  const [selectedScope, setSelectedScope] = useState<'studio' | 'file' | null>(null);
  const [selectedFileId, setSelectedFileId] = useState<string>('');
  const [newConvoTitle, setNewConvoTitle] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    const html = document.documentElement;
  
    // Lock scroll
    html.style.overflow = 'hidden';
  
    return () => {
      // Restore scroll when leaving page
      html.style.overflow = '';
    };
  }, []);

  useEffect(() => {
    fetchQuotas();
  }, [fetchQuotas]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const sidebar = document.getElementById('chat-sidebar');
      const toggleButton = document.getElementById('sidebar-toggle');
      
      if (sidebarOpen && sidebar && toggleButton && 
          !sidebar.contains(e.target as Node) && 
          !toggleButton.contains(e.target as Node)) {
        setSidebarOpen(false);
      }
    };
  
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [sidebarOpen]);

  useEffect(() => {
    if (id && id !== activeConversationId) {
      setActiveConversation(id);
      fetchMessages(id, 10);
    } else if (!id && activeConversationId) {
      setActiveConversation(null);
    }
  }, [id, activeConversationId, setActiveConversation]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || !activeConversationId || isStreaming) return;

    if (!canSendMessage()) {
      toast.error('Insufficient LLM tokens. Please contact developer to increase your quota.');
      return;
    }

    const message = input.trim();
    setInput('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      await sendMessage(activeConversationId, message);
    } catch (error: any) {
      toast.error(error.message || 'Failed to send message');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  };

  const handleCreateConversation = async () => {
    if (!selectedScope) return;
    if (!canCreateConversation()) {
      toast.error("You have reached the maximum number of conversations. Delete unwanted conversations or contact developer.")
    }
    
    const conversationData: any = {
      scope: selectedScope,
      title: newConvoTitle.trim() || undefined,
    };
    
    if (selectedScope === 'file' && selectedFileId) {
      conversationData.file_id = selectedFileId;
    }
    
    try {
      const createdConv = await createConversation(conversationData);
      setActiveConversation(createdConv.id);
      navigate(`/chat/${createdConv.id}`);
    } catch(error: any) {
      toast.error(error.message || "Couldn't create conversation.")
    } finally {
      // Reset form
      resetNewConvoForm();
    }
  };

  const resetNewConvoForm = () => {
    setShowNewConvoDialog(false);
    setSelectedScope(null);
    setSelectedFileId('');
    setNewConvoTitle('');
  };

  if (!activeConversationId) {
    return (
      <div className="flex flex-1">
        
        {!sidebarOpen && (
          <Button
            id="sidebar-toggle-x"
            variant="ghost"
            size="icon"
            className="fixed left-4 top-4 lg:top-16 z-100"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <SB className="h-5 w-5" />
          </Button>
        )}

        {/* Sidebar overlay - clicking outside collapses */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-10 bg-background/80 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <div
          id="chat-sidebar"
          className={cn(
            "fixed left-0 top-0 z-50 h-screen bg-card border-r transition-transform duration-300",
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <Sidebar onClose={() => setSidebarOpen(false)} />
        </div>

        {/* Empty State */}
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <Send className="h-8 w-8 text-secondary translate-x-[-2px]" />
            </div>
            <h2 className="text-2xl font-semibold">No conversation selected</h2>
            <p className="m-4 text-muted-foreground">
              Select a conversation from the sidebar on the left or create a new one to start chatting
            </p>
            <Button className="mt-6" onClick={() => setShowNewConvoDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Conversation
            </Button>
          </div>
        </div>
        
        {/* New Conversation Dialog */}
      <Dialog open={showNewConvoDialog} onOpenChange={() => {setShowNewConvoDialog(false); resetNewConvoForm();}}>
        <DialogContent className="w-[90vw] rounded-xl md:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className='text-sm text-center'>Create New Conversation</DialogTitle>
            <DialogDescription className='text-sm text-center'>
              Choose the scope of conversation you want to create
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Scope Selection */}
            {!selectedScope && (
              <div className="grid grid-cols-1 grid-rows-2 md:grid-cols-2 md:grid-rows-1 gap-4">
                <Card 
                  className="cursor-pointer hover:border-primary transition-colors"
                  onClick={() => setSelectedScope('studio')}
                >
                  <CardHeader>
                    <div className='grid flex-row gap-2 md:flex-col'>
                      <Sparkles className="h-8 w-8 mb-2 text-primary" />
                      <CardTitle className="text-lg">Studio</CardTitle>
                    </div>
                    <CardDescription>
                      General conversation with all files
                    </CardDescription>
                  </CardHeader>
                </Card>
                
                <Card 
                  className="cursor-pointer hover:border-primary transition-colors"
                  onClick={() => setSelectedScope('file')}
                >
                  <CardHeader>
                    <div className='flex flex-row gap-2 md:flex-col'>
                      <FileText className="h-8 w-8 mb-2 text-primary" />
                      <CardTitle className="text-lg">File Chat</CardTitle>
                    </div>
                    <CardDescription>
                      Scope the assistan's search to one file
                    </CardDescription>
                  </CardHeader>
                </Card>
              </div>
            )}

            {/* Form after scope selection */}
            {selectedScope && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  {selectedScope === 'studio' ? <Sparkles className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
                  <span>Creating {selectedScope === 'studio' ? 'Studio' : 'File'} conversation</span>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setSelectedScope(null)}
                    className="ml-auto"
                  >
                    Change
                  </Button>
                </div>

                {selectedScope === 'file' && (
                  <div className="space-y-2">
                  <Label htmlFor="file-select">Select File *</Label>
                
                  <Select.Root
                    value={selectedFileId}
                    onValueChange={(value) => setSelectedFileId(value)}
                  >
                    <Select.Trigger
                      id="file-select"
                      className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    >
                      <Select.Value placeholder="Select a file..." />
                      <Select.Icon>
                        <ChevronDown className="h-4 w-4 opacity-50" />
                      </Select.Icon>
                    </Select.Trigger>
                
                    <Select.Content 
                      className="z-50 max-h-96 overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md"
                      position="popper"
                      align='start'
                      style={{ width: 'var(--radix-select-trigger-width)' }}
                      alignOffset={0}
                      sideOffset={-8}
                    >
                      <Select.Viewport className="p-1">
                        {files.map((file) => (
                          <Select.Item
                            key={file.id}
                            value={file.id}
                            className="flex flex-row justify-between w-full cursor-pointer select-none items-center rounded-sm py-1 px-2 text-sm outline-none focus:bg-primary focus:text-accent-foreground data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground"
                          >
                            <Select.ItemText>{file.name}</Select.ItemText>
                            <Select.ItemIndicator className="flex-end">
                              <Check className="h-4 w-4 text-primary" />
                            </Select.ItemIndicator>
                          </Select.Item>
                        ))}
                      </Select.Viewport>
                    </Select.Content>
                  </Select.Root>
                </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="title">Title (Optional)</Label>
                  <Input
                    id="title"
                    placeholder="Enter conversation title..."
                    value={newConvoTitle}
                    onChange={(e) => setNewConvoTitle(e.target.value)}
                  />
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" className='m-2' onClick={resetNewConvoForm}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateConversation}
              disabled={!selectedScope || (selectedScope === 'file' && !selectedFileId)}
              className='m-2'
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      </div>
    );
  }

  return (
    <div className="flex h-screen flex-1 overflow-hidden justify-center">
      {/* Sidebar toggle - available on all screens */}
      {!sidebarOpen && (<Button
        id="sidebar-toggle"
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 lg:top-16 z-20"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        <SB className="h-5 w-5" />
      </Button>)}

      {/* Sidebar overlay - clicking outside collapses */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-background/80 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        id="chat-sidebar"
        className={cn(
          "fixed left-0 top-0 z-50 h-screen bg-card border-r transition-transform duration-300",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Chat Area - Critical: This must be centered on large screens */}
      <div className="flex flex-1 flex-col overflow-hidden max-h-[98vh] max-w-[95vw] min-h-0">
        {/* Messages Container - Scrollable */}
        <div className="flex-1 overflow-hidden min-h-0">
          <div className="h-full mx-auto max-w-4xl px-4 py-8">
            <MessageList conversationId={activeConversationId} />
          </div>
        </div>

        {/* Input Area - Fixed at bottom */}
        <div className="border-t bg-background">
          <div className="mx-auto max-w-4xl px-4 py-4 lg:py-12">
            <form onSubmit={handleSubmit} className="flex items-end space-x-2">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                disabled={isStreaming}
                className="min-h-[60px] rounded-xl border-slate-500 max-h-[200px] resize-none"
                rows={1}
              />
              <Button
                type="submit"
                variant='default'
                size="icon"
                disabled={!input.trim() || isStreaming}
                className="h-[60px] w-[60px] rounded-full shrink-0"
              >
                {isStreaming ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <ArrowUp className="h-5 w-5" />
                )}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}