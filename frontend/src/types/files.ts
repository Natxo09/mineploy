/**
 * File types
 */

export type FileType = "file" | "directory";

export interface FileInfo {
  name: string;
  path: string;
  type: FileType;
  size: number;
  modified: string | null;
  is_editable: boolean;
  is_deletable: boolean;
  is_renamable: boolean;
  extension: string | null;
}

export interface FileListResponse {
  path: string;
  files: FileInfo[];
  total: number;
}

export interface FileUploadResponse {
  success: boolean;
  path: string;
  size: number;
  message: string;
}

export interface FileDeleteRequest {
  path: string;
}

export interface FileRenameRequest {
  old_path: string;
  new_name: string;
}

export interface CreateFolderRequest {
  path: string;
  name: string;
}

export interface FileContentResponse {
  path: string;
  content: string;
  size: number;
  is_binary: boolean;
}

export interface FileContentUpdate {
  path: string;
  content: string;
}
