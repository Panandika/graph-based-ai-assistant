import type { InputCombinedNodeConfig } from "@/types";
import { InputTextNodeConfig } from "./InputTextNodeConfig";
import { InputImageNodeConfig } from "./InputImageNodeConfig";

interface Props {
  nodeId: string;
  config: InputCombinedNodeConfig;
}

export function InputCombinedNodeConfig({ nodeId, config }: Props) {
  return (
    <div className="mt-2 space-y-4">
      <div className="border-b border-gray-200 pb-3">
        <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">
          Text Input {config.textRequired && <span className="text-red-500">*</span>}
        </h4>
        <InputTextNodeConfig nodeId={nodeId} config={config.textConfig} />
      </div>

      <div>
        <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">
          Image Input {config.imageRequired && <span className="text-red-500">*</span>}
        </h4>
        <InputImageNodeConfig nodeId={nodeId} config={config.imageConfig} />
      </div>
    </div>
  );
}
