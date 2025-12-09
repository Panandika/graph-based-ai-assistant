import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback } from "react";

import { DEFAULT_LLM_CONFIG } from "@/constants/llm";
import { useGraphStore } from "@/store/useGraphStore";
import type { NodeData, NodeType } from "@/types";

import { CustomNode } from "./CustomNode";

const nodeTypes = {
  custom: CustomNode,
};

export function GraphEditor() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, setSelectedNode } =
    useGraphStore();

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node<NodeData>) => {
      setSelectedNode(node.id);
    },
    [setSelectedNode]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData("application/reactflow") as NodeType;
      if (!type) return;

      const position = {
        x: event.clientX - 250,
        y: event.clientY - 100,
      };

      const config = type === "llm" ? { ...DEFAULT_LLM_CONFIG } : {};

      const newNode: Node<NodeData> = {
        id: `${type}-${Date.now()}`,
        type: "custom",
        position,
        data: {
          label: `New ${type}`,
          nodeType: type,
          config,
        },
      };

      addNode(newNode);
    },
    [addNode]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
