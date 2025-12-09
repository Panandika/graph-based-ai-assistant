export type LLMProvider = "openai" | "anthropic";

export interface ModelOption {
  value: string;
  label: string;
}

export const LLM_PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
];

export const MODELS_BY_PROVIDER: Record<LLMProvider, ModelOption[]> = {
  openai: [
    { value: "gpt-4o-mini", label: "GPT-4o Mini" },
    { value: "gpt-4o", label: "GPT-4o" },
  ],
  anthropic: [
    { value: "claude-3-5-sonnet-latest", label: "Claude 3.5 Sonnet" },
    { value: "claude-3-5-haiku-latest", label: "Claude 3.5 Haiku" },
  ],
};

export const DEFAULT_LLM_CONFIG = {
  provider: "openai" as LLMProvider,
  model: "gpt-4o-mini",
  prompt: "",
};
