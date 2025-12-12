export type NodeType =
  | "llm"
  | "tool"
  | "condition"
  | "start"
  | "end"
  | "input_text"
  | "input_image"
  | "input_combined"
  | "llm_transform"
  | "canva_mcp"
  | "output_export";

export interface Position {
  x: number;
  y: number;
}

export interface LLMNodeConfig {
  provider: "openai" | "anthropic" | "google";
  model: string;
  prompt: string;
}

export interface InputTextNodeConfig {
  placeholder?: string;
  maxLength?: number;
  required: boolean;
  defaultValue?: string;
}

export interface InputImageNodeConfig {
  allowUpload: boolean;
  allowUrl: boolean;
  allowClipboard: boolean;
  maxFileSizeMB: number;
  acceptedFormats: string[];
}

export interface InputCombinedNodeConfig {
  textConfig: InputTextNodeConfig;
  imageConfig: InputImageNodeConfig;
  imageRequired: boolean;
  textRequired: boolean;
}

export type InputSource = "upload" | "url" | "clipboard";

export interface TextInput {
  text: string;
  charCount: number;
}

export interface ImageInput {
  source: InputSource;
  url: string;
  base64?: string;
  mimeType: string;
  dimensions?: {
    width: number;
    height: number;
  };
  file?: File;
}

export interface ImageUploadResponse {
  url: string;
  mimeType: string;
  dimensions?: {
    width: number;
    height: number;
  };
  fileSize: number;
  originalFilename?: string;
}

export interface CombinedInput {
  text?: TextInput;
  image?: ImageInput;
}

export interface LLMTransformNodeConfig {
  provider: "openai" | "anthropic" | "google";
  model: string;
  systemPrompt: string;
  userPromptTemplate: string;
  enableVision: boolean;
  imageDetail: "low" | "high" | "auto";
  outputFormat: "text" | "structured";
  generateCanvaInstructions: boolean;
  canvaInstructionPrompt?: string;
  temperature: number;
  maxTokens: number;
}

export type CanvaOperation = "create" | "modify";
export type CanvaOutputFormat = "pdf" | "png" | "jpg" | "link";
export type TemplateSource = "search" | "id" | "from_input";

export interface CanvaMCPNodeConfig {
  operation: CanvaOperation;
  templateSource: TemplateSource;
  templateId?: string;
  templateSearchQuery?: string;
  designName?: string;
  brandKitId?: string;
  outputFormat: CanvaOutputFormat;
  exportQuality?: "standard" | "high";
  timeout: number;
}

export interface CanvaDesignType {
  id: string;
  name: string;
  icon: string;
}

export interface CanvaTemplate {
  id: string;
  title: string;
  thumbnailUrl: string;
  designType: string;
}

export interface CanvaDesignResult {
  designId: string;
  designUrl: string;
  exportUrl?: string;
  thumbnailUrl?: string;
}

export type OutputType = "pdf" | "image" | "link";

export interface OutputExportNodeConfig {
  outputType: OutputType;
  pdfOptions?: {
    pageSize: "A4" | "Letter" | "Original";
    quality: "standard" | "print";
  };
  imageOptions?: {
    format: "png" | "jpg" | "webp";
    quality: number;
    scale: number;
  };
  linkOptions?: {
    accessLevel: "view" | "edit";
    expiresIn?: number;
  };
  downloadAutomatically: boolean;
  showPreview: boolean;
}

export interface OutputExportResult {
  outputType: OutputType;
  url: string;
  filename?: string;
  fileSize?: number;
  previewUrl?: string;
  canvaEditUrl: string;
  expiresAt?: string;
}

export interface NodeData {
  label: string;
  nodeType: NodeType;
  config: Record<string, unknown>;
  [key: string]: unknown;
}

export interface GraphNode {
  id: string;
  type: string;
  position: Position;
  data: NodeData;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  condition?: string;
}

export interface Graph {
  id: string;
  name: string;
  description: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  createdAt: string;
  updatedAt: string;
}

export type WorkflowStatus = "draft" | "active" | "archived";
export type ThreadStatus = "pending" | "running" | "completed" | "failed";

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  graphId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Thread {
  id: string;
  workflowId: string;
  status: ThreadStatus;
  currentNode: string | null;
  inputData: Record<string, unknown>;
  outputData: Record<string, unknown>;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}
