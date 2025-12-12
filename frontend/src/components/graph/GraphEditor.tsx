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
import { TerminalPanel, type LogEntry } from "./TerminalPanel";
import { graphService } from "@/services/graph";
import { useState } from "react";
import { SidebarIcon, TerminalIcon, WindowIcon, PlayIcon } from "../Icons";

interface GraphEditorProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const nodeTypes = {
  custom: CustomNode,
};

export function GraphEditor({ isSidebarOpen, onToggleSidebar }: GraphEditorProps) {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, setSelectedNode } =
    useGraphStore();
  const [isRunning, setIsRunning] = useState(false);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [isFloatingWindowOpen, setIsFloatingWindowOpen] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = (type: LogEntry['type'], message: string, data?: unknown) => {
    setLogs(prev => [...prev, {
      timestamp: Date.now(),
      type,
      message,
      data
    }]);
  };

  const handleRun = async () => {
    if (nodes.length === 0) {
      alert("Please add some nodes first");
      return;
    }

    setIsRunning(true);
    setIsTerminalOpen(true);
    setLogs([]); // Clear previous logs

    try {
      addLog('info', 'Starting graph execution...');

      // 1. Create/Save Graph
      addLog('info', 'Saving graph configuration...');
      const timestamp = Date.now();
      const graph = await graphService.createGraph({
        name: `Graph ${timestamp}`,
        description: "Auto-generated from Run button",
        nodes,
        edges,
      });

      // 2. Create Workflow
      addLog('info', 'Creating workflow context...');
      const workflow = await graphService.createWorkflow({
        name: `Workflow ${timestamp}`,
        description: "Debug execution",
        graph_id: graph.id,
      });

      // 3. Execute Workflow
      addLog('info', 'Initiating execution...');
      const execution = await graphService.executeWorkflow(workflow.id, {
        input_data: {
          prompt: "test run", // Default input for now
        },
      });

      addLog('success', `Execution started. Thread ID: ${execution.thread_id}`);

      // 4. Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await graphService.getThreadStatus(workflow.id, execution.thread_id);

          if (status.status === 'COMPLETED') {
            clearInterval(pollInterval);
            setIsRunning(false);
            addLog('success', 'Execution completed successfully', status.output_data);
          } else if (status.status === 'FAILED') {
            clearInterval(pollInterval);
            setIsRunning(false);
            addLog('error', `Execution failed: ${status.error_message}`);
          } else {
            // Still running, maybe update status if needed
            // addLog('info', `Status: ${status.status}`);
          }
        } catch (error) {
          clearInterval(pollInterval);
          setIsRunning(false);
          addLog('error', 'Failed to poll execution status', error);
        }
      }, 1000);

    } catch (error) {
      console.error("Execution failed:", error);
      addLog('error', 'Failed to start execution', error);
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
      <div className="absolute top-4 right-4 z-10 flex gap-2 items-center">
        <div className="flex bg-white rounded-lg shadow-sm border border-gray-200 p-1 gap-1 mr-2">
          <button
            onClick={onToggleSidebar}
            className={`p-2 rounded hover:bg-gray-100 transition-colors ${!isSidebarOpen ? 'text-blue-500' : 'text-gray-600'}`}
            title={isSidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
          >
            <SidebarIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => setIsTerminalOpen(!isTerminalOpen)}
            className={`p-2 rounded hover:bg-gray-100 transition-colors ${!isTerminalOpen ? 'text-blue-500' : 'text-gray-600'}`}
            title={isTerminalOpen ? "Hide Terminal" : "Show Terminal"}
          >
            <TerminalIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => setIsFloatingWindowOpen(!isFloatingWindowOpen)}
            className={`p-2 rounded hover:bg-gray-100 transition-colors ${isFloatingWindowOpen ? 'text-blue-500' : 'text-gray-600'}`}
            title="Toggle Floating Window"
          >
            <WindowIcon className="w-5 h-5" />
          </button>
        </div>

        <button
          onClick={handleRun}
          disabled={isRunning}
          className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded shadow transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <PlayIcon className="w-4 h-4" />
          {isRunning ? "Running..." : "Run"}
        </button>
      </div>

      {isFloatingWindowOpen && (
        <div className="absolute top-20 right-4 w-80 h-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-sm font-medium text-gray-700">Preview</h3>
            <button
              onClick={() => setIsFloatingWindowOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          <div className="p-4 flex-1 flex items-center justify-center text-gray-400 text-sm">
            Floating Window Content
          </div>
        </div>
      )}
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

      <TerminalPanel
        logs={logs}
        isOpen={isTerminalOpen}
        onToggle={() => setIsTerminalOpen(!isTerminalOpen)}
        onClear={() => setLogs([])}
      />
    </div>
  );
}
