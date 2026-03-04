import { useEffect, useState } from 'react';
import { Upload, Download, Trash2, FileText, FileSpreadsheet, FileDown, MoreVertical, Pencil } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useFilesStore } from '@/stores/files-store';
import { useQuotaStore } from '@/stores/quota-store';
import { toast } from 'sonner';
import { formatBytes, formatRelativeTime } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export default function FilesPage() {
  const { files, processingProgress, isLoading, fetchFiles, uploadFile, deleteFile, downloadFile, updateFile } = useFilesStore();
  const { canUploadFile, quotas, fetchQuotas } = useQuotaStore();
  const [dragging, setDragging] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<string | null>(null);
  const [fileToEdit, setFileToEdit] = useState<any>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadDescription, setUploadDescription] = useState('');
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  useEffect(() => {
    fetchQuotas(true);
  }, [fetchQuotas])

  const handleFileSelect = async (selectedFiles: FileList | null) => {
    // reset state 
    setUploadDialogOpen(false);
    setSelectedFile(null);
    if (!selectedFiles || selectedFiles.length === 0) {
      toast.error('No files selected.')
      return;
    }

    const file = selectedFiles[0];

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      toast.error(`File size exceeds 50MB limit`);
      return;
    }

    // Check quota
    fetchQuotas(true)
    if (!canUploadFile(file.size)) {
      toast.error('Insufficient quota. You need available file slots, processing slots, and storage space.');
      return;
    }

    // Open dialog to get description
    setSelectedFile(file);
    setUploadDescription('');
    setUploadDialogOpen(true);
  };

  const handleUploadConfirm = async () => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    try {
      await uploadFile(selectedFile, {
        name: selectedFile.name,
        description: uploadDescription,
      });
      toast.success('File uploaded successfully!');
      setUploadDialogOpen(false);
      setSelectedFile(null);
      setUploadDescription('');
    } catch (error: any) {
      toast.error(error.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleDownload = async (id: string) => {
    try {
      const url = await downloadFile(id);
      window.open(url, '_blank');
    } catch (error: any) {
      toast.error('Failed to download file');
    }
  };

  const openDeleteDialog = (id: string) => {
    setFileToDelete(id);
    setDeleteDialogOpen(true);
  }

  const handleDeleteConfirm = async () => {
    setIsDeleting(true)
    if (!fileToDelete) return;

    try {
      await deleteFile(fileToDelete);
      toast.success('File deleted');
    } catch (error: any) {
      toast.error(error?.message || 'Failed to delete file');
    } finally {
      setDeleteDialogOpen(false);
      setFileToDelete(null);
      setIsDeleting(false);
    }
  };

  const openEditDialog = (file: any) => {
    setFileToEdit(file);
    setEditName(file.name);
    setEditDescription(file.description || '');
    setEditDialogOpen(true);
  };

  const handleEditConfirm = async () => {
    if (!fileToEdit) return;
    
    setIsUpdating(true);
    try {
      await updateFile(fileToEdit.id, {
        name: editName,
        description: editDescription,
      });
      toast.success('File updated successfully');
      setEditDialogOpen(false);
      setFileToEdit(null);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update file');
    } finally {
      setIsUpdating(false);
    }
  }
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="container mx-auto max-w-6xl space-y-8 p-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold">My Files</h1>
            <p className="mt-2 text-muted-foreground">Manage your uploaded documents</p>
          </div>
          <label htmlFor="file-upload">
            <Button asChild>
              <span>
                <Upload className="mr-2 h-4 w-4" />
                Upload File
              </span>
            </Button>
            <input
              id="file-upload"
              size={2}
              type="file"
              className="hidden"
              onChange={(e) => {
                handleFileSelect(e.target.files);
                e.target.value = '';
              }}
              accept=".pdf,.txt,.md,.xls,.xlsx"
            />
          </label>
        </div>

        {/* Quota Warning */}
        {quotas && (quotas.files === 0 || quotas.file_processing === 0 || quotas.storage_bytes === 0) && (
          <Card className="border-destructive bg-destructive/10">
            <CardContent className="pt-6">
              <p className="text-sm text-destructive">
                ⚠️ Upload blocked: You have reached your quota limit. Contact support to increase your limits.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          className={`rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
            dragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
          }`}
        >
          <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-lg font-medium">Drop files here or click to upload</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Supports PDF, TXT, MD, XLS, XLSX • Max 50MB per file
          </p>
        </div>

        {/* Files List */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Uploaded Files</h2>
          
          {isLoading && files.length === 0 ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i}>
                  <CardContent className="p-6">
                    <Skeleton className="h-20 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : files.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground" />
                <p className="mt-4 text-muted-foreground">No files uploaded yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {files.map((file) => {
                const progress = processingProgress.get(file.id) || 0;
                const isProcessing = file.status === 'processing';

                return (
                  <Card key={file.id}>
                    <CardContent className="p-6">
                      <div className="flex flex-col justify-between w-full">
                        <div className='flex items-start justify-between'>
                          <div className='flex flex-col'>
                            <div className="flex items-center space-x-2">
                                {
                                  ['xls', 'xlsx'].includes(file.extension.toLowerCase()) ? 
                                  ( <FileSpreadsheet className="h-5 w-5 text-green-600 shrink-0" /> )
                                  : file.extension === 'pdf' ? 
                                  (<FileText className="h-5 w-5 text-red-600 shrink-0" />)
                                  : file.extension === 'md' ?
                                  (<FileDown className="h-5 w-5 text-primary shrink-0" />)
                                  : file.extension === 'txt' ?
                                  (<FileText className="h-5 w-5 text-slate-600 shrink-0" />)
                                  : (<FileText className="h-5 w-5 text-primary shrink-0" />)
                                }
                                <p className="font-black truncate">{file.name}</p>
                                <p className='font-sm text-slate-500'>{formatBytes(file.size_bytes)}</p>
                            </div>
                              <p className="mt-1 text-xs text-muted-foreground">
                                {formatRelativeTime(file.created_at)}
                              </p>
                          </div>

                          {/* Context Menu */}
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                size="icon"
                                variant="ghost"
                                className="mx-2 relative left-6 bottom-4"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => openEditDialog(file)}
                              >
                                <Pencil className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDownload(file.id)}
                                disabled={file.status !== 'ready'}
                              >
                                <Download className="mr-2 h-4 w-4" />
                                Download
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => openDeleteDialog(file.id)}
                                className="text-destructive focus:text-destructive"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                        <div className="flex-1 items-start min-w-0">
                          <p className='text-sm mt-2 truncate text-muted-foreground font-medium'>
                            {file.description}
                          </p>
                          
                          {/* Status Badge */}
                          <div className="mt-2 flex gap-4 items-center">
                            <span
                              className={`rounded-xl p-2 text-xs font-medium ${
                                file.status === 'ready'
                                  ? 'bg-green-500/20 text-green-600'
                                  : file.status === 'error'
                                  ? 'bg-red-500/20 text-red-600'
                                  : file.status === 'processing' 
                                  ? "bg-blue-500/20 text-blue-600"
                                  : 'bg-yellow-500/20 text-yellow-600'
                              }`}
                            >
                              {file.status}
                            </span>
                            {/* Processing Progress */}
                            {isProcessing && progress > 0  && (
                              <div className="flex-1">
                                <Progress value={progress} className="h-2" />
                                <p className="text-xs text-muted-foreground">{progress}% processed</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload File</DialogTitle>
            <DialogDescription>
              Add a description to help you remember what this file contains.
              Descriptions are also very useful for the assistant to refine its search and save the costs of searching irrelevant files for studio-scoped conversations.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="upload-filename">File Name</Label>
              <Input
                id="upload-filename"
                value={selectedFile?.name || ''}
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="upload-description">Description (Optional)</Label>
              <Textarea
                id="upload-description"
                placeholder="Enter a description for this file..."
                value={uploadDescription}
                onChange={(e) => setUploadDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setUploadDialogOpen(false);
                setSelectedFile(null);
                setUploadDescription('');
              }}
            >
              Cancel
            </Button>
            <Button disabled={isUploading} onClick={handleUploadConfirm}>
              {isUploading ? 'Uploading...' : 'Upload'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit File</DialogTitle>
            <DialogDescription>
              Update the file name and description.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">File Name</Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="Enter file name..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                placeholder="Enter a description for this file..."
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEditDialogOpen(false);
                setFileToEdit(null);
              }}
            >
              Cancel
            </Button>
            <Button disabled={isUpdating} onClick={handleEditConfirm}>
              {isUpdating ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete File</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this file? All associated conversations will also be deleted. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              className='my-2'
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setFileToDelete(null);
              }}
            >
              Cancel
            </Button>
            <Button disabled={isDeleting} className='my-2' variant="destructive" onClick={handleDeleteConfirm}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}