import { useCallback } from "react";

import {
  DEFAULT_LLM_CONFIG,
  LLM_PROVIDERS,
  MODELS_BY_PROVIDER,
  type LLMProvider,
} from "@/constants/llm";
import { useGraphStore } from "@/store/useGraphStore";

interface LLMNodeConfigProps {
  nodeId: string;
  config: {
    provider?: LLMProvider;
    model?: string;
    prompt?: string;
  };
}

export function LLMNodeConfig({ nodeId, config }: LLMNodeConfigProps) {
  const updateNodeData = useGraphStore((state) => state.updateNodeData);

  const provider = config.provider || DEFAULT_LLM_CONFIG.provider;
  const model = config.model || DEFAULT_LLM_CONFIG.model;
  const prompt = config.prompt || DEFAULT_LLM_CONFIG.prompt;

  const availableModels = MODELS_BY_PROVIDER[provider];

  const handleProviderChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const newProvider = e.target.value as LLMProvider;
      const firstModel = MODELS_BY_PROVIDER[newProvider][0].value;
      updateNodeData(nodeId, {
        config: { ...config, provider: newProvider, model: firstModel },
      });
    },
    [nodeId, config, updateNodeData]
  );

  const handleModelChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      updateNodeData(nodeId, {
        config: { ...config, model: e.target.value },
      });
    },
    [nodeId, config, updateNodeData]
  );

  const handlePromptChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      updateNodeData(nodeId, {
        config: { ...config, prompt: e.target.value },
      });
    },
    [nodeId, config, updateNodeData]
  );

  const stopPropagation = useCallback(
    (e: React.MouseEvent | React.KeyboardEvent) => {
      e.stopPropagation();
    },
    []
  );

  return (
    <div
      className="mt-2 pt-2 border-t border-blue-300 space-y-2"
      onClick={stopPropagation}
      onMouseDown={stopPropagation}
    >
      <div>
        <label className="block text-xs text-gray-600 mb-1">Provider</label>
        <select
          value={provider}
          onChange={handleProviderChange}
          onMouseDown={stopPropagation}
          className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          {LLM_PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs text-gray-600 mb-1">Model</label>
        <select
          value={model}
          onChange={handleModelChange}
          onMouseDown={stopPropagation}
          className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          {availableModels.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs text-gray-600 mb-1">
          Prompt{" "}
          <span className="text-gray-400">
            (use {"{{variable}}"} for interpolation)
          </span>
        </label>
        <textarea
          value={prompt}
          onChange={handlePromptChange}
          onMouseDown={stopPropagation}
          onKeyDown={stopPropagation}
          placeholder="Enter prompt... Use {{input}} for variables"
          rows={3}
          className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-white focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
        />
      </div>
    </div>
  );
}
