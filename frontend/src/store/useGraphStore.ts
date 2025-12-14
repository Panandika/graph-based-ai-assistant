import type { Edge, Node, OnConnect, OnEdgesChange, OnNodesChange } from "@xyflow/react";
import { addEdge, applyEdgeChanges, applyNodeChanges } from "@xyflow/react";
import { create } from "zustand";

import type { NodeData } from "@/types";

interface GraphState {
  nodes: Node<NodeData>[];
  edges: Edge[];
  selectedNodeId: string | null;
  onNodesChange: OnNodesChange<Node<NodeData>>;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  addNode: (node: Node<NodeData>) => void;
  removeNode: (nodeId: string) => void;
  removeEdge: (edgeId: string) => void;
  updateNodeData: (nodeId: string, data: Partial<NodeData>) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setNodes: (nodes: Node<NodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  clear: () => void;
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,

  onNodesChange: (changes) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) });
  },

  onEdgesChange: (changes) => {
    set({ edges: applyEdgeChanges(changes, get().edges) });
  },

  onConnect: (connection) => {
    set({ edges: addEdge(connection, get().edges) });
  },

  addNode: (node) => {
    set({ nodes: [...get().nodes, node] });
  },

  removeNode: (nodeId) => {
    set({
      nodes: get().nodes.filter((n) => n.id !== nodeId),
      edges: get().edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
    });
  },

  removeEdge: (edgeId) => {
    set({
      edges: get().edges.filter((e) => e.id !== edgeId),
    });
  },

  updateNodeData: (nodeId, data) => {
    set({
      nodes: get().nodes.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
      ),
    });
  },

  setSelectedNode: (nodeId) => {
    set({ selectedNodeId: nodeId });
  },

  setNodes: (nodes) => {
    set({ nodes });
  },

  setEdges: (edges) => {
    set({ edges });
  },

  clear: () => {
    set({ nodes: [], edges: [], selectedNodeId: null });
  },
}));
