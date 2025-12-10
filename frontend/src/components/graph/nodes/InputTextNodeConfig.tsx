import { useState } from "react";
import type { InputTextNodeConfig } from "@/types";
import { useGraphStore } from "@/store/useGraphStore";

interface Props {
  nodeId: string;
  config: InputTextNodeConfig;
}

export function InputTextNodeConfig({ nodeId, config }: Props) {
  const updateNodeData = useGraphStore((state) => state.updateNodeData);
  const [text, setText] = useState(config.defaultValue || "");

  const handleTextChange = (value: string) => {
    setText(value);
    updateNodeData(nodeId, {
      value: {
        text: value,
        charCount: value.length,
      },
    });
  };

  const charCount = text.length;
  const maxLength = config.maxLength || Infinity;
  const isOverLimit = charCount > maxLength;

  return (
    <div className="mt-2 space-y-2">
      <textarea
        value={text}
        onChange={(e) => handleTextChange(e.target.value)}
        placeholder={config.placeholder || "Enter text..."}
        maxLength={config.maxLength}
        required={config.required}
        className={`
          w-full px-2 py-1 text-sm border rounded
          focus:outline-none focus:ring-2 focus:ring-blue-400
          ${isOverLimit ? "border-red-500" : "border-gray-300"}
        `}
        rows={3}
      />
      <div className="flex justify-between items-center text-xs">
        <span className={`${isOverLimit ? "text-red-500" : "text-gray-500"}`}>
          {charCount}
          {maxLength !== Infinity && ` / ${maxLength}`} characters
        </span>
        {text && (
          <button
            onClick={() => handleTextChange("")}
            className="text-gray-500 hover:text-gray-700"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
