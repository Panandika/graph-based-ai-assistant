import { ReactFlowProvider } from "@xyflow/react";
import { useState } from "react";

import { GraphEditor } from "@/components/graph/GraphEditor";
import { NodePalette } from "@/components/graph/NodePalette";

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <ReactFlowProvider>
      <div className="flex h-screen overflow-hidden">
        {isSidebarOpen && <NodePalette />}
        <div className="flex-1 relative">
          <GraphEditor
            isSidebarOpen={isSidebarOpen}
            onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          />
        </div>
      </div>
    </ReactFlowProvider>
  );
}

export default App;
