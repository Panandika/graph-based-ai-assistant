import { api } from "./api";
import type { Node, Edge } from "@xyflow/react";
import type { NodeData } from "@/types";

export interface GraphCreate {
    name: string;
    description?: string;
    nodes: Node<NodeData>[];
    edges: Edge[];
}

export interface GraphResponse extends GraphCreate {
    id: string;
    created_at: string;
    updated_at: string;
}

export interface WorkflowCreate {
    name: string;
    description?: string;
    graph_id: string;
}

export interface WorkflowResponse extends WorkflowCreate {
    id: string;
    status: string;
    created_at: string;
    updated_at: string;
}

export interface ExecuteWorkflowRequest {
    input_data: Record<string, unknown>;
}

export interface ExecuteWorkflowResponse {
    thread_id: string;
    status: string;
}

export interface ThreadResponse {
    id: string;
    workflow_id: string;
    status: string;
    current_node?: string;
    input_data?: Record<string, unknown>;
    output_data?: Record<string, unknown>;
    error_message?: string;
    created_at: string;
    updated_at: string;
}

export const graphService = {
    createGraph: (data: GraphCreate) =>
        api.post<GraphResponse>("/graphs", data),

    createWorkflow: (data: WorkflowCreate) =>
        api.post<WorkflowResponse>("/workflows", data),

    executeWorkflow: (workflowId: string, data: ExecuteWorkflowRequest) =>
        api.post<ExecuteWorkflowResponse>(`/workflows/${workflowId}/execute`, data),

    getThreadStatus: (workflowId: string, threadId: string) =>
        api.get<ThreadResponse>(`/workflows/${workflowId}/threads/${threadId}`),
};
