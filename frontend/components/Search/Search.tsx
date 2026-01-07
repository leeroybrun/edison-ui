"use client";

import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import type { KeyboardEvent } from "react";

/** Individual search result item. */
export interface SearchResult {
  /** Result type: task, session, qa, or memory */
  type: "task" | "session" | "qa" | "memory";
  /** Task ID for task results */
  taskId?: string;
  /** Session ID for session results */
  sessionId?: string;
  /** QA ID for QA results */
  qaId?: string;
  /** Title (for tasks) */
  title?: string;
  /** Context snippet */
  snippet: string;
  /** Relevance score 0-1 */
  score: number;
  /** Project ID */
  projectId?: string;
}

/** API response shape for task results. */
interface TaskSearchResult {
  taskId: string;
  title: string;
  snippet: string;
  score: number;
  projectId?: string;
}

/** API response shape for session results. */
interface SessionSearchResult {
  sessionId: string;
  snippet: string;
  score: number;
  projectId?: string;
}

/** API response shape for QA results. */
interface QASearchResult {
  qaId: string;
  taskId: string;
  snippet: string;
  score: number;
  projectId?: string;
}

/** API response shape for memory results. */
interface MemorySearchResult {
  providerId: string;
  text: string;
  score: number;
  meta?: Record<string, unknown>;
}

/** Search API response. */
export interface SearchResponse {
  query: string;
  results: {
    tasks: TaskSearchResult[];
    sessions: SessionSearchResult[];
    qa: QASearchResult[];
    memory: MemorySearchResult[];
  };
  totalHits: number;
}

export interface SearchDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Callback when dialog should close */
  onClose: () => void;
  /** Optional project ID for scoped search */
  projectId?: string;
  /** Callback when a result is selected */
  onSelect?: (result: SearchResult) => void;
  /** API base URL */
  apiBaseUrl?: string;
}

type SearchScope = "all" | "tasks" | "sessions" | "qa" | "memory";

/**
 * SearchDialog provides global or project-scoped search.
 *
 * Features:
 * - Debounced search input
 * - Scope filtering (tasks, sessions, qa, memory)
 * - Keyboard navigation (Arrow keys, Enter, Escape)
 * - Accessible with proper ARIA attributes
 */
export function SearchDialog({
  isOpen,
  onClose,
  projectId,
  onSelect,
  apiBaseUrl = "http://localhost:8000/api/v1",
}: SearchDialogProps) {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<SearchScope>("all");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();
  const abortControllerRef = useRef<AbortController | null>(null);

  // Build API URL based on scope and projectId
  const buildSearchUrl = useCallback(
    (searchQuery: string, searchScope: SearchScope) => {
      const params = new URLSearchParams();
      params.set("q", searchQuery);
      if (searchScope !== "all") {
        params.set("scope", searchScope);
      }

      if (projectId) {
        return `${apiBaseUrl}/projects/${projectId}/search?${params.toString()}`;
      }
      return `${apiBaseUrl}/search?${params.toString()}`;
    },
    [apiBaseUrl, projectId]
  );

  // Transform API response to flat result list
  const transformResponse = useCallback(
    (response: SearchResponse): SearchResult[] => {
      const allResults: SearchResult[] = [];

      for (const task of response.results.tasks) {
        allResults.push({
          type: "task",
          taskId: task.taskId,
          title: task.title,
          snippet: task.snippet,
          score: task.score,
          projectId: task.projectId,
        });
      }

      for (const session of response.results.sessions) {
        allResults.push({
          type: "session",
          sessionId: session.sessionId,
          snippet: session.snippet,
          score: session.score,
          projectId: session.projectId,
        });
      }

      for (const qa of response.results.qa) {
        allResults.push({
          type: "qa",
          qaId: qa.qaId,
          taskId: qa.taskId,
          snippet: qa.snippet,
          score: qa.score,
          projectId: qa.projectId,
        });
      }

      for (const mem of response.results.memory) {
        allResults.push({
          type: "memory",
          snippet: mem.text,
          score: mem.score,
        });
      }

      // Sort by score descending
      return allResults.sort((a, b) => b.score - a.score);
    },
    []
  );

  // Perform search with debounce
  useEffect(() => {
    if (!isOpen || !query.trim()) {
      return;
    }

    const debounceTimeout = setTimeout(async () => {
      // Cancel any pending request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setIsLoading(true);

      try {
        const url = buildSearchUrl(query, scope);
        const response = await fetch(url, {
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Search failed: ${response.status}`);
        }

        const data: SearchResponse = await response.json();
        const transformedResults = transformResponse(data);
        setResults(transformedResults);
        setHasSearched(true);
        setSelectedIndex(-1);
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          return;
        }
        setResults([]);
        setHasSearched(true);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(debounceTimeout);
    };
  }, [query, scope, isOpen, buildSearchUrl, transformResponse]);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setResults([]);
      setHasSearched(false);
      setSelectedIndex(-1);
      setIsLoading(false);
      inputRef.current?.focus();
    } else {
      // Cancel any pending requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    }
  }, [isOpen]);

  const handleSelect = useCallback(
    (result: SearchResult) => {
      onSelect?.(result);
      onClose();
    },
    [onSelect, onClose]
  );

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLInputElement>) => {
      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          setSelectedIndex((prev) => {
            const next = prev + 1;
            return next >= results.length ? 0 : next;
          });
          break;
        case "ArrowUp":
          event.preventDefault();
          setSelectedIndex((prev) => {
            const next = prev - 1;
            return next < 0 ? results.length - 1 : next;
          });
          break;
        case "Enter":
          event.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < results.length) {
            handleSelect(results[selectedIndex]);
          }
          break;
        case "Escape":
          event.preventDefault();
          onClose();
          break;
        case "Tab":
          // Trap focus within dialog
          event.preventDefault();
          break;
      }
    },
    [results, selectedIndex, handleSelect, onClose]
  );

  // Handle global escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Get result display info
  const getResultLabel = useCallback((result: SearchResult): string => {
    if (result.type === "task" && result.title) {
      return result.title;
    }
    if (result.type === "session") {
      return `Session: ${result.sessionId}`;
    }
    if (result.type === "qa") {
      return `QA: ${result.qaId}`;
    }
    return result.snippet.slice(0, 50);
  }, []);

  const getResultIcon = useCallback((type: SearchResult["type"]): string => {
    switch (type) {
      case "task":
        return "📋";
      case "session":
        return "🕐";
      case "qa":
        return "✓";
      case "memory":
        return "💾";
      default:
        return "📄";
    }
  }, []);

  // Calculate active descendant for ARIA
  const activeDescendant = useMemo(() => {
    if (selectedIndex >= 0 && results[selectedIndex]) {
      const result = results[selectedIndex];
      const id = result.taskId || result.sessionId || result.qaId || `result-${selectedIndex}`;
      return `search-result-${id}`;
    }
    return undefined;
  }, [selectedIndex, results]);

  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50"
        data-testid="search-backdrop"
        onClick={onClose}
      />

      {/* Dialog */}
      <div
        aria-label="Search"
        className="fixed left-1/2 top-1/4 z-50 w-full max-w-2xl -translate-x-1/2 transform rounded-lg bg-white shadow-xl"
        role="dialog"
      >
        {/* Search header */}
        <div className="border-b p-4">
          <div className="flex gap-3">
            {/* Scope filter */}
            <div className="flex-shrink-0">
              <label className="sr-only" htmlFor="search-scope">
                Scope
              </label>
              <select
                className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                id="search-scope"
                onChange={(e) => setScope(e.target.value as SearchScope)}
                value={scope}
              >
                <option value="all">All</option>
                <option value="tasks">Tasks</option>
                <option value="sessions">Sessions</option>
                <option value="qa">QA</option>
                <option value="memory">Memory</option>
              </select>
            </div>

            {/* Search input */}
            <input
              aria-activedescendant={activeDescendant}
              aria-autocomplete="list"
              aria-controls={listboxId}
              aria-expanded={results.length > 0}
              autoComplete="off"
              autoFocus
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search tasks, sessions, QA, memory..."
              ref={inputRef}
              role="combobox"
              type="text"
              value={query}
            />
          </div>

          {/* Project scope indicator */}
          {projectId && (
            <p className="mt-2 text-xs text-gray-500">
              Searching within current project
            </p>
          )}
        </div>

        {/* Results */}
        <div className="max-h-96 overflow-y-auto p-2">
          {isLoading && (
            <div className="px-3 py-4 text-center text-sm text-gray-500">
              Searching...
            </div>
          )}

          {!isLoading && hasSearched && results.length === 0 && (
            <div className="px-3 py-4 text-center text-sm text-gray-500">
              No results found
            </div>
          )}

          {!isLoading && !hasSearched && query.length === 0 && (
            <div className="px-3 py-4 text-center text-sm text-gray-500">
              Start typing to search
            </div>
          )}

          {!isLoading && results.length > 0 && (
            <ul id={listboxId} role="listbox">
              {results.map((result, index) => {
                const id =
                  result.taskId ||
                  result.sessionId ||
                  result.qaId ||
                  `result-${index}`;
                const isSelected = selectedIndex === index;

                return (
                  <li
                    aria-selected={isSelected}
                    className={`flex cursor-pointer items-start gap-3 rounded-md px-3 py-2 text-sm ${
                      isSelected
                        ? "bg-blue-100 text-blue-900"
                        : "text-gray-700 hover:bg-gray-100"
                    }`}
                    id={`search-result-${id}`}
                    key={id}
                    onClick={() => handleSelect(result)}
                    onMouseEnter={() => setSelectedIndex(index)}
                    role="option"
                  >
                    <span className="flex-shrink-0 text-lg">
                      {getResultIcon(result.type)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="font-medium">
                        {getResultLabel(result)}
                      </div>
                      <div className="truncate text-xs text-gray-500">
                        {result.snippet}
                      </div>
                      {result.projectId && !projectId && (
                        <div className="mt-1 text-xs text-gray-400">
                          Project: {result.projectId}
                        </div>
                      )}
                    </div>
                    <span className="flex-shrink-0 text-xs text-gray-400">
                      {Math.round(result.score * 100)}%
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-4 py-2 text-xs text-gray-500">
          <kbd className="rounded bg-gray-200 px-1.5 py-0.5 font-mono">↑↓</kbd>
          {" "}navigate{" "}
          <kbd className="rounded bg-gray-200 px-1.5 py-0.5 font-mono">↵</kbd>
          {" "}select{" "}
          <kbd className="rounded bg-gray-200 px-1.5 py-0.5 font-mono">esc</kbd>
          {" "}close
        </div>
      </div>
    </>
  );
}
