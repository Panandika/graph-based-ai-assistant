export const NODE_STYLES = {
    // Input elements (text, number, url, etc.)
    INPUT: "w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-400",

    // Select dropdowns
    SELECT: "w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-400",

    // Textarea
    TEXTAREA: "w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none",

    // Labels
    LABEL: "block text-xs text-gray-600 dark:text-gray-300 mb-1",

    // Headers (like in Combined Node)
    HEADER: "text-xs font-semibold text-gray-700 dark:text-gray-200 uppercase mb-2",

    // Helper text (character counts, loading texts)
    HELPER_TEXT: "text-xs text-gray-500 dark:text-gray-400",

    // Containers
    CONTAINER: "mt-2 pt-2 border-t border-blue-300 dark:border-blue-700 space-y-2",

    // Specific for LLM variables hint
    VARIABLE_HINT: "text-gray-400 dark:text-gray-500",
};

export const NODE_COLORS: Record<string, { bg: string; border: string }> = {
    llm: { bg: "bg-blue-100 dark:bg-blue-900/40", border: "border-blue-500 dark:border-blue-400" },
    tool: { bg: "bg-green-100 dark:bg-green-900/40", border: "border-green-500 dark:border-green-400" },
    condition: { bg: "bg-yellow-100 dark:bg-yellow-900/40", border: "border-yellow-500 dark:border-yellow-400" },
    start: { bg: "bg-gray-100 dark:bg-gray-800", border: "border-gray-500 dark:border-gray-400" },
    end: { bg: "bg-red-100 dark:bg-red-900/40", border: "border-red-500 dark:border-red-400" },
    input_text: { bg: "bg-purple-100 dark:bg-purple-900/40", border: "border-purple-500 dark:border-purple-400" },
    input_image: { bg: "bg-indigo-100 dark:bg-indigo-900/40", border: "border-indigo-500 dark:border-indigo-400" },
    input_combined: { bg: "bg-violet-100 dark:bg-violet-900/40", border: "border-violet-500 dark:border-violet-400" },
    llm_transform: { bg: "bg-blue-100 dark:bg-blue-900/40", border: "border-blue-500 dark:border-blue-400" },
    canva_mcp: { bg: "bg-pink-100 dark:bg-pink-900/40", border: "border-pink-500 dark:border-pink-400" },
    output_export: { bg: "bg-emerald-100 dark:bg-emerald-900/40", border: "border-emerald-500 dark:border-emerald-400" },
    output: { bg: "bg-orange-100 dark:bg-orange-900/40", border: "border-orange-500 dark:border-orange-400" },
};
