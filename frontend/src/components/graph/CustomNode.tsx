import { Handle, Position, type NodeProps } from "@xyflow/react";

import type { LLMProvider } from "@/constants/llm";
import type { NodeData } from "@/types";

import { LLMNodeConfig } from "./LLMNodeConfig";

const nodeStyles: Record<string, { bg: string; border: string }> = {
  llm: { bg: "bg-blue-100", border: "border-blue-500" },
  tool: { bg: "bg-green-100", border: "border-green-500" },
  condition: { bg: "bg-yellow-100", border: "border-yellow-500" },
  start: { bg: "bg-gray-100", border: "border-gray-500" },
  end: { bg: "bg-red-100", border: "border-red-500" },
};

export function CustomNode({ id, data, selected }: NodeProps) {
  const nodeData = data as NodeData;
  const style = nodeStyles[nodeData.nodeType] || nodeStyles.start;
  const isLLMNode = nodeData.nodeType === "llm";

  return (
    <div
      className={`
        px-4 py-2 rounded-lg border-2
        ${isLLMNode ? "min-w-[280px]" : "min-w-[120px]"}
        ${style.bg} ${style.border}
        ${selected ? "ring-2 ring-blue-400" : ""}
      `}
    >
      {nodeData.nodeType !== "start" && (
        <Handle type="target" position={Position.Top} className="w-3 h-3" />
      )}

      <div className="text-center">
        <div className="text-xs text-gray-500 uppercase">{nodeData.nodeType}</div>
        <div className="font-medium">{nodeData.label}</div>
      </div>

      {isLLMNode && (
        <LLMNodeConfig
          nodeId={id}
          config={
            nodeData.config as {
              provider?: LLMProvider;
              model?: string;
              prompt?: string;
            }
          }
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
