"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fileService } from "@/services/file.service";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  FolderOpen,
  File,
  Loader2,
  Upload,
  Download,
  FolderPlus,
  Trash2,
  Edit,
  ChevronRight,
  Home,
  RefreshCcw,
  FileText,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import type { FileInfo } from "@/types";
import { FileEditorDialog } from "./file-editor-dialog";

interface ServerFilesProps {
  serverId: number;
  isRunning: boolean;
}

export function ServerFiles({ serverId, isRunning }: ServerFilesProps) {
  const [currentPath, setCurrentPath] = useState("/");
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);

  // Dialogs
  const [createFolderOpen, setCreateFolderOpen] = useState(false);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Form states
  const [folderName, setFolderName] = useState("");
  const [newName, setNewName] = useState("");
  const [fileContent, setFileContent] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch files (works whether server is running or not, just needs container)
  const { data: fileList, isLoading, refetch } = useQuery({
    queryKey: ["files", serverId, currentPath],
    queryFn: () => fileService.listFiles(serverId, currentPath),
    enabled: true, // Always enabled if server has a container
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => fileService.uploadFile(serverId, file, currentPath),
    onSuccess: () => {
      toast.success("File uploaded successfully");
      queryClient.invalidateQueries({ queryKey: ["files", serverId, currentPath] });
    },
    onError: (error: any) => {
      toast.error("Upload failed", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (path: string) => fileService.deleteFile(serverId, { path }),
    onSuccess: () => {
      toast.success("Deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["files", serverId, currentPath] });
      setDeleteDialogOpen(false);
      setSelectedFile(null);
    },
    onError: (error: any) => {
      toast.error("Delete failed", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  // Create folder mutation
  const createFolderMutation = useMutation({
    mutationFn: (name: string) =>
      fileService.createFolder(serverId, { path: currentPath, name }),
    onSuccess: () => {
      toast.success("Folder created successfully");
      queryClient.invalidateQueries({ queryKey: ["files", serverId, currentPath] });
      setCreateFolderOpen(false);
      setFolderName("");
    },
    onError: (error: any) => {
      toast.error("Failed to create folder", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  // Rename mutation
  const renameMutation = useMutation({
    mutationFn: ({ old_path, new_name }: { old_path: string; new_name: string }) =>
      fileService.renameFile(serverId, { old_path, new_name }),
    onSuccess: () => {
      toast.success("Renamed successfully");
      queryClient.invalidateQueries({ queryKey: ["files", serverId, currentPath] });
      setRenameDialogOpen(false);
      setSelectedFile(null);
      setNewName("");
    },
    onError: (error: any) => {
      toast.error("Rename failed", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  // Update file content mutation
  const updateContentMutation = useMutation({
    mutationFn: ({ path, content }: { path: string; content: string }) =>
      fileService.updateFileContent(serverId, { path, content }),
    onSuccess: () => {
      toast.success("File saved successfully");
      setEditDialogOpen(false);
      setSelectedFile(null);
      setFileContent("");
    },
    onError: (error: any) => {
      toast.error("Save failed", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    },
  });

  // Handlers
  const handleFileClick = (file: FileInfo) => {
    if (file.type === "directory") {
      setCurrentPath(file.path);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
    // Reset input
    event.target.value = "";
  };

  const handleDownload = async (file: FileInfo) => {
    try {
      const blob = await fileService.downloadFile(serverId, file.path);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Download started");
    } catch (error: any) {
      toast.error("Download failed", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    }
  };

  const handleEdit = async (file: FileInfo) => {
    try {
      const response = await fileService.getFileContent(serverId, file.path);
      setFileContent(response.content);
      setSelectedFile(file);
      setEditDialogOpen(true);
    } catch (error: any) {
      toast.error("Failed to load file", {
        description: error?.response?.data?.detail || "An error occurred",
      });
    }
  };

  const handleDelete = (file: FileInfo) => {
    setSelectedFile(file);
    setDeleteDialogOpen(true);
  };

  const handleRename = (file: FileInfo) => {
    setSelectedFile(file);
    setNewName(file.name);
    setRenameDialogOpen(true);
  };

  const confirmDelete = () => {
    if (selectedFile) {
      deleteMutation.mutate(selectedFile.path);
    }
  };

  const confirmRename = () => {
    if (selectedFile && newName.trim()) {
      renameMutation.mutate({ old_path: selectedFile.path, new_name: newName.trim() });
    }
  };

  const confirmCreateFolder = () => {
    if (folderName.trim()) {
      createFolderMutation.mutate(folderName.trim());
    }
  };

  const confirmSaveFile = () => {
    if (selectedFile) {
      updateContentMutation.mutate({ path: selectedFile.path, content: fileContent });
    }
  };

  const navigateToParent = () => {
    if (currentPath === "/") return;
    const parts = currentPath.split("/").filter(Boolean);
    parts.pop();
    setCurrentPath(parts.length > 0 ? "/" + parts.join("/") : "/");
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "-";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  // Breadcrumb
  const pathParts = currentPath.split("/").filter(Boolean);

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <FolderOpen className="size-6" />
              File Manager
            </h2>
            <p className="text-muted-foreground">
              Browse, upload, and manage server files
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCcw className={cn("size-4", isLoading && "animate-spin")} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCreateFolderOpen(true)}
            >
              <FolderPlus className="size-4" />
              New Folder
            </Button>
            <Button
              size="sm"
              onClick={handleUploadClick}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Upload className="size-4" />
              )}
              Upload File
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileUpload}
            />
          </div>
        </div>

        <Separator />

        <Card className="py-0">
            {/* Breadcrumb */}
            <div className="px-4 py-3 border-b flex items-center gap-2 text-sm">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2"
                onClick={() => setCurrentPath("/")}
              >
                <Home className="size-4" />
              </Button>
              {currentPath !== "/" && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2"
                  onClick={navigateToParent}
                >
                  ..
                </Button>
              )}
              {pathParts.map((part, index) => (
                <div key={index} className="flex items-center gap-2">
                  <ChevronRight className="size-4 text-muted-foreground" />
                  <span className="font-medium">{part}</span>
                </div>
              ))}
            </div>

            {/* File Table */}
            {isLoading ? (
              <div className="p-12 flex items-center justify-center">
                <Loader2 className="size-8 animate-spin text-muted-foreground" />
              </div>
            ) : fileList && fileList.files.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Modified</TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fileList.files.map((file) => (
                    <ContextMenu key={file.path}>
                      <ContextMenuTrigger asChild>
                        <TableRow
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => handleFileClick(file)}
                        >
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              {file.type === "directory" ? (
                                <FolderOpen className="size-4 text-blue-500" />
                              ) : file.is_editable ? (
                                <FileText className="size-4 text-green-500" />
                              ) : (
                                <File className="size-4 text-muted-foreground" />
                              )}
                              <span>{file.name}</span>
                              {file.extension && (
                                <Badge variant="outline" className="text-xs">
                                  {file.extension}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {formatFileSize(file.size)}
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {formatDate(file.modified)}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              {file.type === "file" && (
                                <>
                                  {file.is_editable && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-7 w-7 p-0"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleEdit(file);
                                      }}
                                    >
                                      <Edit className="size-3.5" />
                                    </Button>
                                  )}
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 w-7 p-0"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDownload(file);
                                    }}
                                  >
                                    <Download className="size-3.5" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      </ContextMenuTrigger>
                      <ContextMenuContent>
                        {file.type === "file" && file.is_editable && (
                          <>
                            <ContextMenuItem onClick={() => handleEdit(file)}>
                              <Edit className="size-4 mr-2" />
                              Edit
                            </ContextMenuItem>
                            <ContextMenuSeparator />
                          </>
                        )}
                        {file.type === "file" && (
                          <ContextMenuItem onClick={() => handleDownload(file)}>
                            <Download className="size-4 mr-2" />
                            Download
                          </ContextMenuItem>
                        )}
                        <ContextMenuItem
                          onClick={() => handleRename(file)}
                          disabled={!file.is_renamable}
                        >
                          <Edit className="size-4 mr-2" />
                          Rename
                          {!file.is_renamable && " (Protected)"}
                        </ContextMenuItem>
                        <ContextMenuSeparator />
                        <ContextMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => handleDelete(file)}
                          disabled={!file.is_deletable}
                        >
                          <Trash2 className="size-4 mr-2" />
                          Delete
                          {!file.is_deletable && " (Protected)"}
                        </ContextMenuItem>
                      </ContextMenuContent>
                    </ContextMenu>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="p-12 flex flex-col items-center justify-center text-center gap-2">
                <FolderOpen className="size-12 text-muted-foreground" />
                <p className="text-muted-foreground">No files in this directory</p>
              </div>
            )}
          </Card>
      </div>

      {/* Create Folder Dialog */}
      <Dialog open={createFolderOpen} onOpenChange={setCreateFolderOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Folder</DialogTitle>
            <DialogDescription>
              Create a new folder in {currentPath}
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="Folder name"
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") confirmCreateFolder();
            }}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateFolderOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={confirmCreateFolder}
              disabled={!folderName.trim() || createFolderMutation.isPending}
            >
              {createFolderMutation.isPending && (
                <Loader2 className="size-4 animate-spin mr-2" />
              )}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename</DialogTitle>
            <DialogDescription>
              Rename {selectedFile?.name}
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="New name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") confirmRename();
            }}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={confirmRename}
              disabled={!newName.trim() || renameMutation.isPending}
            >
              {renameMutation.isPending && (
                <Loader2 className="size-4 animate-spin mr-2" />
              )}
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete {selectedFile?.name}.
              {selectedFile?.type === "directory" && " All contents will be deleted."}
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending && (
                <Loader2 className="size-4 animate-spin mr-2" />
              )}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit/View File Dialog */}
      <FileEditorDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        fileName={selectedFile?.name || ""}
        filePath={selectedFile?.path || ""}
        fileExtension={selectedFile?.extension || undefined}
        content={fileContent}
        isEditable={selectedFile?.is_editable || false}
        isSaving={updateContentMutation.isPending}
        onSave={confirmSaveFile}
      />
    </>
  );
}
