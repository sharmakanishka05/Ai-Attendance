"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, Image as ImageIcon, X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onFileSelect,
  selectedFile,
  onClear,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setError(null);

    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type)) {
      setError("Please upload a valid image (JPG, PNG, or WEBP).");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setError("File is too large. Maximum supported upload is 15MB.");
      return;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    onFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const clearSelection = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setError(null);
    onClear();
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="w-full text-left">
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {error && (
        <div className="mb-3 p-3 bg-danger-subtle border border-danger-border rounded-control text-danger text-[13px] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {selectedFile && previewUrl ? (
        <div className="bg-white border border-border rounded-card p-4">
          <div className="relative rounded-card overflow-hidden bg-subtle aspect-video flex items-center justify-center border border-border/80">
            <img
              src={previewUrl}
              alt="Classroom photo preview"
              className="w-full h-full object-contain"
            />
            <button
              onClick={clearSelection}
              aria-label="Remove image"
              className="absolute top-3 right-3 p-1.5 bg-black/60 hover:bg-black/80 text-white rounded-full transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-3 flex items-center justify-between text-[13px]">
            <div className="truncate pr-2">
              <span className="font-medium text-primary-text block truncate">
                {selectedFile.name}
              </span>
              <span className="text-secondary-text text-[11px]">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => inputRef.current?.click()}
            >
              Replace Photo
            </Button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-card p-8 text-center cursor-pointer transition-colors duration-150 ${
            isDragging
              ? "border-accent bg-accent-subtle/40"
              : "border-border hover:border-border-hover bg-white hover:bg-subtle/50"
          }`}
        >
          <div className="w-10 h-10 rounded-full bg-subtle text-secondary-text mx-auto flex items-center justify-center mb-3">
            <UploadCloud className="w-5 h-5 text-accent" />
          </div>
          <div className="text-[14px] font-medium text-primary-text">
            Drop classroom photo here
          </div>
          <div className="text-[12px] text-secondary-text mt-1">
            or <span className="text-accent underline underline-offset-2">Browse files</span> from your computer
          </div>
          <div className="text-[11px] text-muted-text mt-3">
            Supports single or multi-person classroom photos (JPG, PNG, WEBP up to 15MB)
          </div>
        </div>
      )}
    </div>
  );
};
