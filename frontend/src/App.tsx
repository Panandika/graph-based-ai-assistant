import { ReactFlowProvider } from "@xyflow/react";

import { GraphEditor } from "@/components/graph/GraphEditor";
import { NodePalette } from "@/components/graph/NodePalette";

function App() {
  return (
    <ReactFlowProvider>
      <div className="flex h-screen">
        <NodePalette />
        <div className="flex-1">
          <GraphEditor />
        </div>
      </div>
    </ReactFlowProvider>
  );
}

export default App;
