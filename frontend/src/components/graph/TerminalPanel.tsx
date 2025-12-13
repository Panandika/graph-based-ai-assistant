import { useEffect, useRef, useState, useCallback } from 'react';

export interface LogEntry {
    timestamp: number;
    type: 'info' | 'success' | 'error' | 'warning' | 'link' | 'image';
    message: string;
    data?: unknown;
}

interface TerminalPanelProps {
    logs: LogEntry[];
    isOpen: boolean;
    onToggle: () => void;
    onClear: () => void;
}

const TerminalIcon = ({ size = 24, className = "" }: { size?: number, className?: string }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <polyline points="4 17 10 11 4 5"></polyline>
        <line x1="12" y1="19" x2="20" y2="19"></line>
    </svg>
);

const MinimizeIcon = ({ size = 24 }: { size?: number }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <line x1="4" y1="14" x2="10" y2="14"></line>
        <line x1="10" y1="14" x2="10" y2="20"></line>
        <line x1="20" y1="10" x2="14" y2="10"></line>
        <line x1="14" y1="10" x2="14" y2="4"></line>
    </svg>
);

const LinkIcon = ({ size = 16 }: { size?: number }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
    </svg>
);

const ImageIcon = ({ size = 16 }: { size?: number }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
        <circle cx="8.5" cy="8.5" r="1.5"></circle>
        <polyline points="21 15 16 10 5 21"></polyline>
    </svg>
);

export function TerminalPanel({ logs, isOpen, onToggle, onClear }: TerminalPanelProps) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [height, setHeight] = useState(384); // Default to h-96 (24rem * 16px = 384px)
    const [isResizing, setIsResizing] = useState(false);

    useEffect(() => {
        if (scrollRef.current && isOpen) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, isOpen]);

    const startResizing = useCallback(() => {
        setIsResizing(true);
    }, []);

    const stopResizing = useCallback(() => {
        setIsResizing(false);
    }, []);

    const resize = useCallback(
        (e: MouseEvent) => {
            if (isResizing) {
                // Calculate new height based on distance from bottom
                const newHeight = window.innerHeight - e.clientY;
                // Constraints: Min 100px, Max 80% of screen
                if (newHeight >= 100 && newHeight <= window.innerHeight * 0.8) {
                    setHeight(newHeight);
                }
            }
        },
        [isResizing]
    );

    useEffect(() => {
        if (isResizing) {
            window.addEventListener('mousemove', resize);
            window.addEventListener('mouseup', stopResizing);
        }
        return () => {
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        };
    }, [isResizing, resize, stopResizing]);

    const renderLogContent = (log: LogEntry) => {
        switch (log.type) {
            case 'link':
                return (
                    <div className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors">
                        <LinkIcon />
                        <a href={log.data as string} target="_blank" rel="noopener noreferrer" className="underline decoration-blue-400/30 hover:decoration-blue-400">
                            {log.message}
                        </a>
                    </div>
                );
            case 'image':
                return (
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-purple-400">
                            <ImageIcon />
                            <span>{log.message}</span>
                        </div>
                        <div className="rounded-lg overflow-hidden border border-gray-800 bg-gray-900/50 max-w-sm">
                            <img
                                src={log.data as string}
                                alt={log.message}
                                className="w-full h-auto"
                                loading="lazy"
                            />
                        </div>
                    </div>
                );
            default:
                return (
                    <>
                        <div className={`
                            ${log.type === 'error' ? 'text-red-400' : ''}
                            ${log.type === 'success' ? 'text-green-400' : ''}
                            ${log.type === 'warning' ? 'text-yellow-400' : ''}
                            ${log.type === 'info' ? 'text-blue-400' : ''}
                        `}>
                            {log.type === 'success' && '✓ '}
                            {log.type === 'error' && '✗ '}
                            {log.message}
                        </div>
                        {log.data !== undefined && (
                            <pre className="mt-1 p-2 bg-gray-900/50 rounded text-xs overflow-x-auto text-gray-300 font-mono">
                                {typeof log.data === 'string' ? log.data : JSON.stringify(log.data, null, 2)}
                            </pre>
                        )}
                    </>
                );
        }
    };

    if (!isOpen) {
        return null;
    }

    return (
        <div
            className="absolute bottom-0 left-0 right-0 bg-gray-950 text-gray-200 border-t border-gray-800 shadow-2xl z-20 flex flex-col font-mono text-sm"
            style={{ height: `${height}px` }}
        >
            {/* Drag Handle */}
            <div
                onMouseDown={startResizing}
                className="w-full h-1 bg-gray-800 hover:bg-blue-500 cursor-ns-resize transition-colors flex justify-center items-center group relative -mt-0.5"
            >
                <div className="w-8 h-1 bg-gray-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity absolute" />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800 select-none">
                <div className="flex items-center gap-2">
                    <TerminalIcon size={16} className="text-blue-400" />
                    <span className="font-semibold text-gray-100">Execution Output</span>
                    {logs.length > 0 && (
                        <span className="text-xs bg-gray-800 px-2 py-0.5 rounded text-gray-400">
                            {logs.length} lines
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={onClear}
                        className="text-xs px-2 py-1 hover:bg-gray-800 rounded text-gray-400 hover:text-white transition-colors"
                    >
                        Clear
                    </button>
                    <button
                        onClick={onToggle}
                        className="p-1 hover:bg-gray-800 rounded text-gray-400 hover:text-white transition-colors"
                    >
                        <MinimizeIcon size={16} />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-3 font-mono"
            >
                {logs.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-2">
                        <TerminalIcon size={32} className="opacity-20" />
                        <div className="italic">Ready for execution...</div>
                    </div>
                ) : (
                    logs.map((log, index) => (
                        <div key={index} className="flex gap-3 items-start animate-in fade-in slide-in-from-bottom-1 duration-200">
                            <span className="text-gray-600 shrink-0 text-xs mt-1 select-none">
                                [{new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
                            </span>
                            <div className="flex-1 min-w-0 break-words">
                                {renderLogContent(log)}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
