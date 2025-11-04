"use client";

import { useState, useEffect } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import Editor from "react-simple-code-editor";
import Prism from "prismjs";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-jsx";
import "prismjs/components/prism-tsx";
import "prismjs/components/prism-json";
import "prismjs/components/prism-yaml";
import "prismjs/components/prism-markup";
import "prismjs/components/prism-bash";
import "prismjs/components/prism-python";
import "prismjs/components/prism-java";
import "prismjs/components/prism-markdown";
import "prismjs/components/prism-ini";
import "prismjs/components/prism-toml";
import "prismjs/components/prism-properties";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Eye, Edit as EditIcon, Save, X } from "lucide-react";

interface FileEditorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  fileName: string;
  filePath: string;
  fileExtension?: string;
  content: string;
  isEditable: boolean;
  isSaving?: boolean;
  onSave?: (content: string) => void;
}

// Map file extensions to Prism language names
const getPrismLanguage = (extension?: string): string => {
  if (!extension) return "text";

  const languageMap: Record<string, string> = {
    js: "javascript",
    jsx: "jsx",
    ts: "typescript",
    tsx: "tsx",
    json: "json",
    yml: "yaml",
    yaml: "yaml",
    xml: "markup",
    properties: "properties",
    conf: "nginx",
    cfg: "ini",
    ini: "ini",
    toml: "toml",
    sh: "bash",
    bash: "bash",
    py: "python",
    java: "java",
    md: "markdown",
    txt: "text",
    log: "text",
  };

  return languageMap[extension.toLowerCase()] || "text";
};

// Highlight code using Prism
const highlightCode = (code: string, language: string) => {
  try {
    if (language === "text") {
      return code;
    }

    // Check if language exists, otherwise try fallbacks
    let prismLang = Prism.languages[language];

    if (!prismLang) {
      // Fallback for properties to ini
      if (language === "properties") {
        prismLang = Prism.languages.ini;
      }

      // If still no language found, return plain text
      if (!prismLang) {
        return code;
      }
    }

    return Prism.highlight(code, prismLang, language);
  } catch (error) {
    console.error("Prism highlighting error:", error);
    return code;
  }
};

export function FileEditorDialog({
  open,
  onOpenChange,
  fileName,
  filePath,
  fileExtension,
  content,
  isEditable,
  isSaving = false,
  onSave,
}: FileEditorDialogProps) {
  const [editedContent, setEditedContent] = useState(content);
  const [activeTab, setActiveTab] = useState<"view" | "edit">(
    isEditable ? "edit" : "view"
  );

  // Reset content when dialog opens or content changes
  useEffect(() => {
    setEditedContent(content);
  }, [content]);

  // Reset to view tab for read-only files
  useEffect(() => {
    if (!isEditable) {
      setActiveTab("view");
    }
  }, [isEditable]);

  const handleSave = () => {
    if (onSave) {
      onSave(editedContent);
    }
  };

  const handleCancel = () => {
    setEditedContent(content);
    onOpenChange(false);
  };

  const hasChanges = editedContent !== content;
  const language = getPrismLanguage(fileExtension);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-7xl w-[85vw] h-[85vh] flex flex-col p-0">
        {/* Header */}
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <DialogTitle className="text-xl flex items-center gap-2">
                {fileName}
                {!isEditable && (
                  <Badge variant="outline" className="text-xs font-normal">
                    Read Only
                  </Badge>
                )}
              </DialogTitle>
              <DialogDescription className="font-mono text-xs">
                {filePath}
              </DialogDescription>
            </div>
            {fileExtension && (
              <Badge variant="secondary" className="text-xs">
                {fileExtension.toUpperCase()}
              </Badge>
            )}
          </div>
        </DialogHeader>

        {/* Content */}
        <div className="flex-1 overflow-hidden px-6">
          {isEditable ? (
            <Tabs
              value={activeTab}
              onValueChange={(value) => setActiveTab(value as "view" | "edit")}
              className="h-full flex flex-col"
            >
              <TabsList className="grid w-[240px] grid-cols-2 mb-4">
                <TabsTrigger value="edit" className="gap-2">
                  <EditIcon className="size-3.5" />
                  Edit
                </TabsTrigger>
                <TabsTrigger value="view" className="gap-2">
                  <Eye className="size-3.5" />
                  Preview
                </TabsTrigger>
              </TabsList>

              <TabsContent value="edit" className="flex-1 mt-0 overflow-hidden">
                <ScrollArea className="h-full w-full rounded-md border">
                  <Editor
                    value={editedContent}
                    onValueChange={setEditedContent}
                    highlight={(code) => highlightCode(code, language)}
                    padding={16}
                    className="font-mono text-sm min-h-full"
                    style={{
                      fontFamily: '"Fira code", "Fira Mono", monospace',
                      fontSize: 14,
                      backgroundColor: "#1e1e1e",
                      color: "#d4d4d4",
                      minHeight: "100%",
                    }}
                    textareaClassName="focus:outline-none"
                  />
                </ScrollArea>
              </TabsContent>

              <TabsContent value="view" className="flex-1 mt-0 overflow-hidden">
                <ScrollArea className="h-full w-full rounded-md border">
                  <SyntaxHighlighter
                    language={language}
                    style={vscDarkPlus}
                    customStyle={{
                      margin: 0,
                      borderRadius: "0.375rem",
                      fontSize: "0.875rem",
                    }}
                    showLineNumbers
                    wrapLines
                  >
                    {editedContent}
                  </SyntaxHighlighter>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          ) : (
            // Read-only view
            <ScrollArea className="h-full w-full rounded-md border">
              <SyntaxHighlighter
                language={language}
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  borderRadius: "0.375rem",
                  fontSize: "0.875rem",
                }}
                showLineNumbers
                wrapLines
              >
                {content}
              </SyntaxHighlighter>
            </ScrollArea>
          )}
        </div>

        {/* Footer */}
        <DialogFooter className="px-6 pb-6 pt-4 border-t">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              {hasChanges && isEditable && (
                <Badge variant="outline" className="text-xs">
                  Unsaved changes
                </Badge>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleCancel}>
                <X className="size-4" />
                {hasChanges ? "Cancel" : "Close"}
              </Button>
              {isEditable && (
                <Button
                  onClick={handleSave}
                  disabled={!hasChanges || isSaving}
                >
                  {isSaving ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Save className="size-4" />
                  )}
                  Save Changes
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
