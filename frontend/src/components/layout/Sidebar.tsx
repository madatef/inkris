import { Plus, ChevronDown, Check, ChevronRight, FileText, Sparkles, MoreHorizontal, X, Trash2, Pencil } from 'lucide-react';
import * as Select from '@radix-ui/react-select'
import { Button } from '../ui/button';
import { toast } from 'sonner';
import { useChatStore } from '@/stores/chat-store';
import { useFilesStore } from '@/stores/files-store';
import { useQuotaStore } from '@/stores/quota-store';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { formatRelativeTime } from '@/lib/utils';
import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

interface SidebarProps {
  onClose: () => void;
}

export default function Sidebar({onClose}: SidebarProps) {
  const navigate = useNavigate();
  const {
    conversations, fetchConversations, 
    activeConversationId, setActiveConversation, 
    deleteConversation, renameConversation,
     fetchMessages, createConversation,
  } = useChatStore();
  const { canCreateConversation, fetchQuotas} = useQuotaStore()
  const { files, fetchFiles } = useFilesStore();
  const [studioOpen, setStudioOpen] = useState(true);
  const [filesOpen, setFilesOpen] = useState(true);
  // Dialog states
  const [showNewConvoDialog, setShowNewConvoDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showRenameDialog, setShowRenameDialog] = useState(false);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  
  // New conversation form state
  const [selectedScope, setSelectedScope] = useState<'studio' | 'file' | null>(null);
  const [selectedFileId, setSelectedFileId] = useState<string>('');
  const [newConvoTitle, setNewConvoTitle] = useState('');

  useEffect(() => {
    fetchConversations(1, 50);
  }, [fetchConversations]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles])

  useEffect(() => {
    fetchQuotas(true);
  }, [fetchQuotas])

  const studioConversations = conversations.filter(c => c.scope === 'studio');
  const fileConversations = conversations.filter(c => c.scope === 'file');

  const handleConversationClick = (id: string) => {
    setActiveConversation(id);
    fetchMessages(id, 10);
    navigate(`/chat/${id}`);
  };

  const openRenameDialog = (id: string, currentTitle: string | null) => {
    setSelectedConversationId(id);
    setRenameValue(currentTitle || '');
    setShowRenameDialog(true);
  };

  const handleRenameSubmit = async () => {
    if (selectedConversationId && renameValue.trim()) {
      try {
        await renameConversation(selectedConversationId, renameValue.trim());
      } catch(error: any) {
        toast.error(error.message || "Couldn't rename conversation.")
      } finally {
        setShowRenameDialog(false);
        setSelectedConversationId(null);
        setRenameValue('');
      }
    }
  };

  const openDeleteDialog = (id: string) => {
    setSelectedConversationId(id);
    setShowDeleteDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (selectedConversationId) {
      try {
        await deleteConversation(selectedConversationId);
        toast.success('Conversation deleted.');
        setSelectedConversationId(null);
        if (activeConversationId === selectedConversationId) { setActiveConversation(null); navigate('/chat') }
      } catch(error: any) {
        toast.error(error.message || "Couldn't delete conversation.")
      } finally {
        setShowDeleteDialog(false);
      }
    }
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
      setActiveConversation(createdConv.id)
      navigate(`/chat/${createdConv.id}`)
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

  return (
    <div className="flex w-64 flex-col border-r bg-card">
      {/* Header */}
      <div className="flex flex-col items-center justify-center border-b p-4">
        <div className='flex justify-between w-full mb-2 mx-0 px-0'>
          <span className="font-semibold">Conversations</span>
          <Button 
            variant="ghost"
            size="icon"
            className="h-full"
            onClick={onClose}
          >
            <X className='h-5 w-5 text-destructive'></X>
          </Button>
        </div>
        <Button size="sm" className="w-full" onClick={() => setShowNewConvoDialog(true)}>
          <Plus className="h-4 w-4 mr-1" />
          New Conversation
        </Button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {/* Studio Conversations */}
        <div className="border-b">
          <button
            onClick={() => setStudioOpen(!studioOpen)}
            className="flex w-full items-center justify-between px-4 py-3 hover:bg-accent"
          >
            <div className="flex items-center space-x-2">
              <Sparkles className="h-4 w-4" />
              <span className="font-medium">Studio</span>
              <span className="text-xs text-muted-foreground">({studioConversations.length})</span>
            </div>
            {studioOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
          {studioOpen && (
            <div className="space-y-1 p-2">
              {studioConversations.map((conv) => (
                <div
                  key={conv.id}
                  className={cn(
                    "group flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer transition-colors",
                    activeConversationId === conv.id ? "bg-primary/10" : "hover:bg-accent"
                  )}
                  onClick={() => handleConversationClick(conv.id)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {conv.title || 'Untitled conversation'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatRelativeTime(conv.updated_at)}
                    </p>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent sideOffset={-8} align="end">
                      <DropdownMenuItem className='mt-2' onClick={(e) => { e.stopPropagation(); openRenameDialog(conv.id, conv.title); }}>
                        <Pencil className="mr-2 h-4 w-4" />
                        Rename
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); openDeleteDialog(conv.id); }} 
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
              {studioConversations.length === 0 && (
                <p className="px-3 py-2 text-sm text-muted-foreground">No conversations yet</p>
              )}
            </div>
          )}
        </div>

        {/* File Conversations */}
        <div>
          <button
            onClick={() => setFilesOpen(!filesOpen)}
            className="flex w-full items-center justify-between px-4 py-3 hover:bg-accent"
          >
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4" />
              <span className="font-medium">File Chats</span>
              <span className="text-xs text-muted-foreground">({fileConversations.length})</span>
            </div>
            {filesOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
          {filesOpen && (
            <div className="space-y-1 p-2">
              {fileConversations.map((conv) => {
                const file = files.find(f => f.id === conv.file_id);
                const displayTitle = conv.title || (file ? `Untitled - ${file.name}` : 'Untitled conversation');
                
                return (
                  <div
                    key={conv.id}
                    className={cn(
                      "group flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer transition-colors",
                      activeConversationId === conv.id ? "bg-primary/10" : "hover:bg-accent"
                    )}
                    onClick={() => handleConversationClick(conv.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{displayTitle}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatRelativeTime(conv.updated_at)}
                      </p>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent sideOffset={-8} align="end">
                        <DropdownMenuItem className='mt-2' onClick={(e) => { e.stopPropagation(); openRenameDialog(conv.id, conv.title); }}>
                          <Pencil className="mr-2 h-4 w-4" />
                          Rename
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={(e) => { e.stopPropagation(); openDeleteDialog(conv.id); }}
                          className="text-destructive focus:text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                );
              })}
              {fileConversations.length === 0 && (
                <p className="px-3 py-2 text-sm text-muted-foreground">No file chats yet</p>
              )}
            </div>
          )}
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this conversation? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rename Dialog */}
      <Dialog open={showRenameDialog} onOpenChange={setShowRenameDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Conversation</DialogTitle>
            <DialogDescription>
              Enter a new title for this conversation
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              placeholder="Enter new title..."
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleRenameSubmit();
                }
              }}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRenameDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleRenameSubmit} disabled={!renameValue.trim()}>
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}