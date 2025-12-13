export const config = {
    API_BASE_URL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
    ENV: import.meta.env.MODE,
    IS_DEV: import.meta.env.DEV,
    IS_PROD: import.meta.env.PROD,
};
