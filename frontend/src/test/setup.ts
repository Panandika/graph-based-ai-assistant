import "@testing-library/jest-dom/vitest";

// Mock ResizeObserver for @xyflow/react
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock;
