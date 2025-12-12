import { ReactFlowProvider } from "@xyflow/react";
import { useState } from "react";

import { GraphEditor } from "@/components/graph/GraphEditor";
import { NodePalette } from "@/components/graph/NodePalette";
import { ToastProvider } from "@/components/ui/ToastContext";

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <ReactFlowProvider>
      <ToastProvider>
        <div className="flex h-screen overflow-hidden">
          {isSidebarOpen && <NodePalette />}
          <div className="flex-1 relative">
            <GraphEditor
              isSidebarOpen={isSidebarOpen}
              onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
            />
          </div>
        </div>
      </ToastProvider>
    </ReactFlowProvider>
  );
}

export default App;
