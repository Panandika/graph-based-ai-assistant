import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useReactFlow,
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
import { useToast } from "@/components/ui/ToastContext";
import { SidebarIcon, TerminalIcon, WindowIcon, PlayIcon } from "../Icons";

interface GraphEditorProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const nodeTypes = {
  custom: CustomNode,
};

export function GraphEditor({ isSidebarOpen, onToggleSidebar }: GraphEditorProps) {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, removeEdge, setSelectedNode } =
    useGraphStore();
  const { screenToFlowPosition } = useReactFlow();
  const [isRunning, setIsRunning] = useState(false);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [isFloatingWindowOpen, setIsFloatingWindowOpen] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const { toast } = useToast();

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
      toast({ type: 'warning', message: "Please add some nodes first" });
      return;
    }

    setIsRunning(true);
    setIsTerminalOpen(true);
    setLogs([]); // Clear previous logs

    try {
      addLog('info', 'Initializing execution environment...');

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
        description: "Execution triggered from editor",
        graph_id: graph.id,
      });

      // 3. Execute Workflow
      addLog('info', 'Sending execution request...');

      // We send empty input_data, relying on nodes to use their own configuration
      const execution = await graphService.executeWorkflow(workflow.id, {
        input_data: {},
      });

      addLog('success', `Execution started. Thread ID: ${execution.thread_id.slice(0, 8)}...`);
      toast({ type: 'success', message: 'Execution started successfully' });

      // 4. Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await graphService.getThreadStatus(workflow.id, execution.thread_id);

          if (status.status === 'completed') {
            clearInterval(pollInterval);
            setIsRunning(false);

            // Check for specific outputs to display nicely
            const outputData = status.output_data as Record<string, any>;

            if (outputData.final_output) {
              addLog('success', 'Execution completed successfully');
              const final = outputData.final_output;

              if (final.url) {
                addLog('link', 'Access your design:', final.url);
                if (final.type === 'image' || final.url.match(/\.(jpeg|jpg|gif|png)$/i)) {
                  addLog('image', 'Design Preview:', final.url);
                }
              }

              if (final.edit_url) {
                addLog('link', 'Edit in Canva:', final.edit_url);
              }

            } else if (outputData.canva_design_url) {
              addLog('success', 'Execution completed successfully');
              addLog('link', 'Canva Design URL:', outputData.canva_design_url);
              if (outputData.canva_export_url) {
                addLog('link', 'Export URL:', outputData.canva_export_url);
                addLog('image', 'Export Preview:', outputData.canva_export_url);
              }
            } else {
              addLog('success', 'Execution completed successfully', outputData);
            }

            toast({ type: 'success', message: 'Execution completed' });
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsRunning(false);
            addLog('error', `Execution failed: ${status.error_message}`);
            toast({ type: 'error', message: `Execution failed: ${status.error_message}` });
          } else {
            // Still running
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
      toast({ type: 'error', message: "Failed to start execution" });
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

      // Use screenToFlowPosition to convert screen coordinates to flow coordinates
      // This properly accounts for canvas offset, pan, and zoom
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

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
    [addNode, screenToFlowPosition]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onEdgeDoubleClick = useCallback(
    (_: React.MouseEvent, edge: { id: string }) => {
      removeEdge(edge.id);
    },
    [removeEdge]
  );

  return (
    <div className="w-full h-full relative">
      <div className="absolute top-4 right-4 z-10 flex gap-2 items-center">
        <div className="flex bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-1 gap-1 mr-2 transition-colors">
          <button
            onClick={onToggleSidebar}
            className={`p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${!isSidebarOpen ? 'text-blue-500' : 'text-gray-600 dark:text-gray-300'}`}
            title={isSidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
          >
            <SidebarIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => setIsTerminalOpen(!isTerminalOpen)}
            className={`p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${!isTerminalOpen ? 'text-blue-500' : 'text-gray-600 dark:text-gray-300'}`}
            title={isTerminalOpen ? "Hide Terminal" : "Show Terminal"}
          >
            <TerminalIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => setIsFloatingWindowOpen(!isFloatingWindowOpen)}
            className={`p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${isFloatingWindowOpen ? 'text-blue-500' : 'text-gray-600 dark:text-gray-300'}`}
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
        <div className="absolute top-20 right-4 w-80 h-64 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          <div className="bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-200">Preview</h3>
            <button
              onClick={() => setIsFloatingWindowOpen(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ×
            </button>
          </div>
          <div className="p-4 flex-1 flex items-center justify-center text-gray-400 dark:text-gray-500 text-sm">
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
        onEdgeDoubleClick={onEdgeDoubleClick}
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
