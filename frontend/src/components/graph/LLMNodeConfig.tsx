import { useCallback } from "react";

import {
  DEFAULT_LLM_CONFIG,
  LLM_PROVIDERS,
  MODELS_BY_PROVIDER,
  type LLMProvider,
} from "@/constants/llm";
import { NODE_STYLES } from "@/constants/styles";
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
      className={NODE_STYLES.CONTAINER}
      onClick={stopPropagation}
      onMouseDown={stopPropagation}
    >
      <div>
        <label className={NODE_STYLES.LABEL}>Provider</label>
        <select
          value={provider}
          onChange={handleProviderChange}
          onMouseDown={stopPropagation}
          className={NODE_STYLES.SELECT}
        >
          {LLM_PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className={NODE_STYLES.LABEL}>Model</label>
        <select
          value={model}
          onChange={handleModelChange}
          onMouseDown={stopPropagation}
          className={NODE_STYLES.SELECT}
        >
          {availableModels.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className={NODE_STYLES.LABEL}>
          Prompt{" "}
          <span className={NODE_STYLES.VARIABLE_HINT}>
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
          className={NODE_STYLES.TEXTAREA}
        />
      </div>
    </div>
  );
}

