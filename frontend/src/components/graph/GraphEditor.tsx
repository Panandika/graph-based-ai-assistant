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
import { graphService } from "@/services/graph";
import { useState } from "react";

const nodeTypes = {
  custom: CustomNode,
};

export function GraphEditor() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, setSelectedNode } =
    useGraphStore();
  const [isRunning, setIsRunning] = useState(false);

  const handleRun = async () => {
    if (nodes.length === 0) {
      alert("Please add some nodes first");
      return;
    }

    setIsRunning(true);
    try {
      // 1. Create/Save Graph
      const timestamp = Date.now();
      const graph = await graphService.createGraph({
        name: `Graph ${timestamp}`,
        description: "Auto-generated from Run button",
        nodes,
        edges,
      });

      // 2. Create Workflow
      const workflow = await graphService.createWorkflow({
        name: `Workflow ${timestamp}`,
        description: "Debug execution",
        graph_id: graph.id,
      });

      // 3. Execute Workflow
      const execution = await graphService.executeWorkflow(workflow.id, {
        input_data: {
          prompt: "test run", // Default input for now
        },
      });

      console.log("Execution started:", execution);
      alert(`Execution started! Thread ID: ${execution.thread_id}`);
    } catch (error) {
      console.error("Execution failed:", error);
      alert("Failed to start execution. Check console for details.");
    } finally {
      setIsRunning(false);
    }
  };

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
    <div className="w-full h-full relative">
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded shadow transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning ? "Running..." : "Run Graph"}
        </button>
      </div>
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
