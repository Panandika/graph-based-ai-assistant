import { useState, useRef, useCallback } from "react";
import type { InputImageNodeConfig, ImageInput } from "@/types";
import { useGraphStore } from "@/store/useGraphStore";
import { uploadImage, fetchImageFromUrl } from "@/services/uploadService";
import { NODE_STYLES } from "@/constants/styles";

interface Props {
  nodeId: string;
  config: InputImageNodeConfig;
}

export function InputImageNodeConfig({ nodeId, config }: Props) {
  const updateNodeData = useGraphStore((state) => state.updateNodeData);
  const [imageData, setImageData] = useState<ImageInput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  const handleImageLoaded = useCallback(
    (data: ImageInput) => {
      setImageData(data);
      setError(null);
      updateNodeData(nodeId, {
        value: {
          image: data,
        },
      });
    },
    [nodeId, updateNodeData]
  );

  const handleFileUpload = useCallback(
    async (file: File) => {
      if (file.size > config.maxFileSizeMB * 1024 * 1024) {
        setError(`File size exceeds ${config.maxFileSizeMB}MB limit`);
        return;
      }

      const fileType = file.type;
      if (!config.acceptedFormats.includes(fileType)) {
        setError(
          `File format not supported. Accepted: ${config.acceptedFormats.join(", ")}`
        );
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await uploadImage(file);
        handleImageLoaded({
          source: "upload",
          url: response.url,
          mimeType: response.mimeType,
          dimensions: response.dimensions,
          file,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to upload image");
      } finally {
        setIsLoading(false);
      }
    },
    [config.maxFileSizeMB, config.acceptedFormats, handleImageLoaded]
  );

  const handleUrlSubmit = useCallback(async () => {
    if (!urlInput.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const sessionId = `node-${nodeId}`;
      const response = await fetchImageFromUrl(urlInput.trim(), sessionId);
      handleImageLoaded({
        source: "url",
        url: response.url,
        mimeType: response.mimeType,
        dimensions: response.dimensions,
      });
      setUrlInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch image");
    } finally {
      setIsLoading(false);
    }
  }, [urlInput, nodeId, handleImageLoaded]);

  const handlePaste = useCallback(
    async (e: React.ClipboardEvent) => {
      if (!config.allowClipboard) return;

      const items = e.clipboardData.items;
      for (const item of Array.from(items)) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) {
            e.preventDefault();
            await handleFileUpload(file);
            break;
          }
        }
      }
    }
    ,
    [config.allowClipboard, handleFileUpload]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (!config.allowUpload) return;

      const files = Array.from(e.dataTransfer.files);
      const imageFile = files.find((f) => f.type.startsWith("image/"));

      if (imageFile) {
        await handleFileUpload(imageFile);
      }
    },
    [config.allowUpload, handleFileUpload]
  );

  const handleClear = useCallback(() => {
    setImageData(null);
    setError(null);
    setUrlInput("");
    updateNodeData(nodeId, {
      value: {
        image: null,
      },
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [nodeId, updateNodeData]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="mt-2 space-y-2" onPaste={handlePaste}>
      {!imageData ? (
        <>
          {config.allowUpload && (
            <div
              ref={dropZoneRef}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded p-4 text-center hover:border-indigo-400 dark:hover:border-indigo-400 transition-colors bg-gray-50 dark:bg-gray-800/50"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={config.acceptedFormats.join(",")}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium"
              >
                Click to upload
              </button>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                or drag and drop
                {config.allowClipboard && " or paste from clipboard"}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                Max {config.maxFileSizeMB}MB
              </p>
            </div>
          )}

          {config.allowUrl && (
            <div className="flex gap-2">
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleUrlSubmit()}
                placeholder="Or enter image URL..."
                className={NODE_STYLES.INPUT}
              />
              <button
                onClick={handleUrlSubmit}
                disabled={!urlInput.trim() || isLoading}
                className="px-3 py-1 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Load
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="space-y-2">
          <div className="relative">
            <img
              src={imageData.url}
              alt="Preview"
              className="w-full h-32 object-cover rounded border border-gray-300 dark:border-gray-600"
            />
            <button
              onClick={handleClear}
              className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 text-xs shadow-sm"
            >
              &times;
            </button>
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
            <div className="flex justify-between">
              <span>Source:</span>
              <span className="font-medium capitalize">{imageData.source}</span>
            </div>
            {imageData.dimensions && (
              <div className="flex justify-between">
                <span>Dimensions:</span>
                <span className="font-medium">
                  {imageData.dimensions.width} x {imageData.dimensions.height}
                </span>
              </div>
            )}
            {imageData.file && (
              <div className="flex justify-between">
                <span>Size:</span>
                <span className="font-medium">
                  {formatFileSize(imageData.file.size)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="text-center py-2">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 dark:border-indigo-400"></div>
          <p className={NODE_STYLES.HELPER_TEXT}>Loading image...</p>
        </div>
      )}

      {error && (
        <div className="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}
    </div>
  );
}

