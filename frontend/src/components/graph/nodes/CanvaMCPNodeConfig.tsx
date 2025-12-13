import { useEffect, useState } from "react";
import { config } from "@/config/env";

interface CanvaMCPNodeConfigProps {
    nodeId: string;
    config?: any;
}

export function CanvaMCPNodeConfig({ nodeId, config: _config }: CanvaMCPNodeConfigProps) {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [loading, setLoading] = useState(true);

    const checkAuth = async () => {
        try {
            // API_BASE_URL usually includes /api/v1
            const response = await fetch(`${config.API_BASE_URL}/auth/canva/status`);
            if (response.ok) {
                const data = await response.json();
                setIsAuthenticated(data.authenticated);
            }
        } catch (error) {
            console.error("Failed to check auth status", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
        // Poll every 5 seconds if not authenticated
        let interval: ReturnType<typeof setInterval>;
        if (!isAuthenticated) {
            interval = setInterval(checkAuth, 5000);
        }
        return () => clearInterval(interval);
    }, [isAuthenticated]);

    const handleConnect = () => {
        // Open login in new tab
        const loginUrl = `${config.API_BASE_URL}/auth/canva/login`;
        console.log("Opening Canva Auth URL:", loginUrl);
        window.open(loginUrl, "_blank", "width=600,height=700");
    };

    if (loading) {
        return <div className="p-2 text-xs text-center text-gray-500">Checking connection...</div>;
    }

    if (!isAuthenticated) {
        return (
            <div className="p-2 flex flex-col items-center gap-2">
                <div className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                    Authentication Required
                </div>
                <button
                    onClick={handleConnect}
                    className="px-3 py-1 bg-[#00C4CC] hover:bg-[#00B2B9] text-white text-xs font-bold rounded shadow-sm transition-colors w-full"
                >
                    Connect to Canva
                </button>
            </div>
        );
    }

    return (
        <div className="p-2 flex flex-col items-center gap-2">
            <div className="text-xs text-green-600 dark:text-green-400 font-medium flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Connected
            </div>
            <div className="text-[10px] text-gray-400">
                Ready to create designs
            </div>
        </div>
    );
}
