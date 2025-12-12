import { AlertCircleIcon, CheckCircleIcon, InfoIcon, XIcon } from '@/components/Icons';
import { ToastType } from './ToastContext';

interface ToastProps {
    type: ToastType;
    title?: string;
    message: string;
    onDismiss: () => void;
}

const icons = {
    success: <CheckCircleIcon className="w-5 h-5 text-green-500" />,
    error: <AlertCircleIcon className="w-5 h-5 text-red-500" />,
    warning: <AlertCircleIcon className="w-5 h-5 text-yellow-500" />,
    info: <InfoIcon className="w-5 h-5 text-blue-500" />,
};

const bgColors = {
    success: 'bg-white border-l-4 border-green-500',
    error: 'bg-white border-l-4 border-red-500',
    warning: 'bg-white border-l-4 border-yellow-500',
    info: 'bg-white border-l-4 border-blue-500',
};

export function Toast({ type, title, message, onDismiss }: ToastProps) {
    return (
        <div className={`${bgColors[type]} p-4 rounded shadow-lg border flex items-start gap-3 min-w-[300px] animate-in slide-in-from-right fade-in duration-300`}>
            <div className="flex-shrink-0 mt-0.5">
                {icons[type]}
            </div>
            <div className="flex-1">
                {title && <h3 className="font-medium text-gray-900">{title}</h3>}
                <p className="text-sm text-gray-500 mt-0.5">{message}</p>
            </div>
            <button
                onClick={onDismiss}
                className="ml-4 text-gray-400 hover:text-gray-500 focus:outline-none"
            >
                <XIcon className="w-4 h-4" />
            </button>
        </div>
    );
}
