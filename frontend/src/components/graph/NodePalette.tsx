import type { NodeType } from "@/types";

interface PaletteItem {
  type: NodeType;
  label: string;
  color: string;
}

const paletteItems: PaletteItem[] = [
  { type: "start", label: "Start", color: "bg-gray-200" },
  { type: "input_text", label: "Text Input", color: "bg-purple-200" },
  { type: "input_image", label: "Image Input", color: "bg-indigo-200" },
  { type: "input_combined", label: "Combined Input", color: "bg-violet-200" },
  { type: "llm", label: "LLM", color: "bg-blue-200" },
  { type: "llm_transform", label: "LLM Transform", color: "bg-blue-300" },
  { type: "tool", label: "Tool", color: "bg-green-200" },
  { type: "canva_mcp", label: "Canva MCP", color: "bg-pink-200" },
  { type: "condition", label: "Condition", color: "bg-yellow-200" },
  { type: "output", label: "Output", color: "bg-orange-200" },
  { type: "output_export", label: "Output Export", color: "bg-emerald-200" },
  { type: "end", label: "End", color: "bg-red-200" },
];

export function NodePalette() {
  const onDragStart = (event: React.DragEvent, nodeType: NodeType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <div className="p-4 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 w-48 transition-colors">
      <h3 className="font-semibold mb-4 text-gray-900 dark:text-gray-100">Nodes</h3>
      <div className="space-y-2">
        {paletteItems.map((item) => (
          <div
            key={item.type}
            className={`
              p-2 rounded cursor-grab border border-gray-300 dark:border-gray-700
              ${item.color}
              text-gray-900 dark:text-gray-900 font-medium
              hover:opacity-80 transition-all
            `}
            draggable
            onDragStart={(e) => onDragStart(e, item.type)}
          >
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}
