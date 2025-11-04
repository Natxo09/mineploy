import apiClient from "@/lib/api-client";
import type {
  FileListResponse,
  FileUploadResponse,
  FileDeleteRequest,
  FileRenameRequest,
  CreateFolderRequest,
  FileContentResponse,
  FileContentUpdate,
} from "@/types";

/**
 * File management service
 */
export const fileService = {
  /**
   * List files in a directory
   */
  async listFiles(serverId: number, path: string = "/"): Promise<FileListResponse> {
    const response = await apiClient.get<FileListResponse>(
      `/servers/${serverId}/files`,
      { params: { path } }
    );
    return response.data;
  },

  /**
   * Get file content for editing
   */
  async getFileContent(serverId: number, path: string): Promise<FileContentResponse> {
    const response = await apiClient.get<FileContentResponse>(
      `/servers/${serverId}/files/content`,
      { params: { path } }
    );
    return response.data;
  },

  /**
   * Update file content
   */
  async updateFileContent(
    serverId: number,
    data: FileContentUpdate
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.put(
      `/servers/${serverId}/files/content`,
      data
    );
    return response.data;
  },

  /**
   * Download a file
   */
  async downloadFile(serverId: number, path: string): Promise<Blob> {
    const response = await apiClient.get(
      `/servers/${serverId}/files/download`,
      {
        params: { path },
        responseType: "blob",
      }
    );
    return response.data;
  },

  /**
   * Upload a file
   */
  async uploadFile(
    serverId: number,
    file: File,
    path: string = "/"
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<FileUploadResponse>(
      `/servers/${serverId}/files/upload`,
      formData,
      {
        params: { path },
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * Delete a file or directory
   */
  async deleteFile(
    serverId: number,
    data: FileDeleteRequest
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(`/servers/${serverId}/files`, {
      data,
    });
    return response.data;
  },

  /**
   * Create a new folder
   */
  async createFolder(
    serverId: number,
    data: CreateFolderRequest
  ): Promise<{ success: boolean; message: string; path: string }> {
    const response = await apiClient.post(
      `/servers/${serverId}/files/folder`,
      data
    );
    return response.data;
  },

  /**
   * Rename a file or directory
   */
  async renameFile(
    serverId: number,
    data: FileRenameRequest
  ): Promise<{ success: boolean; message: string; new_path: string }> {
    const response = await apiClient.post(
      `/servers/${serverId}/files/rename`,
      data
    );
    return response.data;
  },
};
