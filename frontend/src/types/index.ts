export type NodeType = "llm" | "tool" | "condition" | "start" | "end";

export interface Position {
  x: number;
  y: number;
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
