import type { NodeType } from "@/types";

interface PaletteItem {
  type: NodeType;
  label: string;
  color: string;
}

const paletteItems: PaletteItem[] = [
  { type: "start", label: "Start", color: "bg-gray-200" },
  { type: "llm", label: "LLM", color: "bg-blue-200" },
  { type: "tool", label: "Tool", color: "bg-green-200" },
  { type: "condition", label: "Condition", color: "bg-yellow-200" },
  { type: "end", label: "End", color: "bg-red-200" },
];

export function NodePalette() {
  const onDragStart = (event: React.DragEvent, nodeType: NodeType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <div className="p-4 bg-white border-r border-gray-200 w-48">
      <h3 className="font-semibold mb-4">Nodes</h3>
      <div className="space-y-2">
        {paletteItems.map((item) => (
          <div
            key={item.type}
            className={`
              p-2 rounded cursor-grab border border-gray-300
              ${item.color} hover:opacity-80 transition-opacity
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
