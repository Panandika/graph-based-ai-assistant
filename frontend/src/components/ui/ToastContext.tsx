import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { Toast } from './Toast';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastMessage {
    id: string;
    type: ToastType;
    title?: string;
    message: string;
    duration?: number;
}

interface ToastContextType {
    toast: (props: Omit<ToastMessage, 'id'>) => void;
    dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const dismiss = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const toast = useCallback(
        ({ type, title, message, duration = 3000 }: Omit<ToastMessage, 'id'>) => {
            const id = Math.random().toString(36).substring(2, 9);
            const newToast = { id, type, title, message, duration };

            setToasts((prev) => [...prev, newToast]);

            if (duration > 0) {
                setTimeout(() => {
                    dismiss(id);
                }, duration);
            }
        },
        [dismiss]
    );

    return (
        <ToastContext.Provider value={{ toast, dismiss }}>
            {children}
            {toasts.length > 0 &&
                createPortal(
                    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm pointer-events-none">
                        {toasts.map((t) => (
                            <div key={t.id} className="pointer-events-auto">
                                <Toast
                                    type={t.type}
                                    title={t.title}
                                    message={t.message}
                                    onDismiss={() => dismiss(t.id)}
                                />
                            </div>
                        ))}
                    </div>,
                    document.body
                )
            }
        </ToastContext.Provider>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
}
