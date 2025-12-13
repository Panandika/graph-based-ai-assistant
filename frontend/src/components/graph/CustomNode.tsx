import { Handle, Position, type NodeProps } from "@xyflow/react";

import type { LLMProvider } from "@/constants/llm";
import { NODE_COLORS } from "@/constants/styles";
import type {
  NodeData,
  InputTextNodeConfig as InputTextNodeConfigType,
  InputImageNodeConfig as InputImageNodeConfigType,
  InputCombinedNodeConfig as InputCombinedNodeConfigType,
} from "@/types";

import { useGraphStore } from "@/store/useGraphStore";
import { LLMNodeConfig } from "./LLMNodeConfig";
import { InputTextNodeConfig } from "./nodes/InputTextNodeConfig";
import { InputImageNodeConfig } from "./nodes/InputImageNodeConfig";
import { InputCombinedNodeConfig } from "./nodes/InputCombinedNodeConfig";
import { CanvaMCPNodeConfig } from "./nodes/CanvaMCPNodeConfig";

export function CustomNode({ id, data, selected }: NodeProps) {
  const { removeNode } = useGraphStore();
  const nodeData = data as NodeData;
  const style = NODE_COLORS[nodeData.nodeType] || NODE_COLORS.start;
  const hasConfig =
    nodeData.nodeType === "llm" ||
    nodeData.nodeType === "input_text" ||
    nodeData.nodeType === "input_image" ||
    nodeData.nodeType === "input_combined" ||
    nodeData.nodeType === "canva_mcp" ||
    nodeData.nodeType === "llm_transform";

  return (
    <div
      className={`
        px-4 py-2 rounded-lg border-2 relative group
        ${hasConfig ? "min-w-[280px]" : "min-w-[120px]"}
        ${style.bg} ${style.border}
        ${selected ? "ring-2 ring-blue-400" : ""}
      `}
    >
      <button
        className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full text-white 
                 flex items-center justify-center opacity-0 group-hover:opacity-100 
                 transition-opacity hover:bg-red-600 shadow-sm z-50"
        onClick={(e) => {
          e.stopPropagation();
          removeNode(id);
        }}
        title="Delete node"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 6 6 18" />
          <path d="m6 6 12 12" />
        </svg>
      </button>

      {nodeData.nodeType !== "start" && (
        <Handle type="target" position={Position.Top} className="w-3 h-3" />
      )}

      <div className="text-center">
        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">
          {nodeData.nodeType.replace(/_/g, " ")}
        </div>
        <div className="font-medium">{nodeData.label}</div>
      </div>

      {(nodeData.nodeType === "llm" || nodeData.nodeType === "llm_transform") && (
        <LLMNodeConfig
          nodeId={id}
          config={
            nodeData.config as unknown as {
              provider?: LLMProvider;
              model?: string;
              prompt?: string;
            }
          }
        />
      )}

      {nodeData.nodeType === "input_text" && (
        <InputTextNodeConfig
          nodeId={id}
          config={nodeData.config as unknown as InputTextNodeConfigType}
        />
      )}

      {nodeData.nodeType === "input_image" && (
        <InputImageNodeConfig
          nodeId={id}
          config={nodeData.config as unknown as InputImageNodeConfigType}
        />
      )}

      {nodeData.nodeType === "input_combined" && (
        <InputCombinedNodeConfig
          nodeId={id}
          config={nodeData.config as unknown as InputCombinedNodeConfigType}
        />
      )}

      {nodeData.nodeType === "canva_mcp" && (
        <CanvaMCPNodeConfig
          nodeId={id}
          config={nodeData.config}
        />
      )}

      {nodeData.nodeType !== "end" && (
        <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
      )}

      {nodeData.nodeType === "condition" && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            className="w-3 h-3"
            style={{ top: "50%" }}
          />
          <Handle
            type="source"
            position={Position.Left}
            id="false"
            className="w-3 h-3"
            style={{ top: "50%" }}
          />
        </>
      )}
    </div>
  );
}

