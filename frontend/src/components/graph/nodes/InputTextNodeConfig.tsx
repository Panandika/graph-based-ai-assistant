import { useState } from "react";
import type { InputTextNodeConfig } from "@/types";
import { useGraphStore } from "@/store/useGraphStore";
import { NODE_STYLES } from "@/constants/styles";

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
        className={`${NODE_STYLES.TEXTAREA} ${isOverLimit ? "border-red-500" : ""}`}
        rows={3}
      />
      <div className="flex justify-between items-center text-xs">
        <span className={`${isOverLimit ? "text-red-500" : NODE_STYLES.HELPER_TEXT}`}>
          {charCount}
          {maxLength !== Infinity && ` / ${maxLength}`} characters
        </span>
        {text && (
          <button
            onClick={() => handleTextChange("")}
            className={`${NODE_STYLES.HELPER_TEXT} hover:text-gray-700 dark:hover:text-gray-300`}
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

