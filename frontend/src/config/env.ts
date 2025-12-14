const getApiBaseUrl = () => {
    const url = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    if (url.endsWith("/")) {
        return url.slice(0, -1);
    }
    return url.endsWith("/api/v1") ? url : `${url}/api/v1`;
};

export const config = {
    API_BASE_URL: getApiBaseUrl(),
    ENV: import.meta.env.MODE,
    IS_DEV: import.meta.env.DEV,
    IS_PROD: import.meta.env.PROD,
};
