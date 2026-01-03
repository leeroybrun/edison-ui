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

/**
 * Command definition for the command palette
 */
export interface Command {
  /** Unique identifier for the command */
  id: string;
  /** Display label for the command */
  label: string;
  /** Optional keyboard shortcut hint */
  shortcut?: string;
  /** Action to execute when command is selected */
  action: () => void;
  /** Category for grouping commands */
  category: string;
}

export interface CommandPaletteProps {
  /** Available commands */
  commands: Command[];
  /** Whether the palette is open */
  isOpen: boolean;
  /** Callback when palette should close */
  onClose: () => void;
}

/**
 * Simple fuzzy match function
 * Returns true if all characters in query appear in text in order
 */
function fuzzyMatch(query: string, text: string): boolean {
  const lowerQuery = query.toLowerCase();
  const lowerText = text.toLowerCase();

  let queryIndex = 0;
  for (let i = 0; i < lowerText.length && queryIndex < lowerQuery.length; i++) {
    if (lowerText[i] === lowerQuery[queryIndex]) {
      queryIndex++;
    }
  }
  return queryIndex === lowerQuery.length;
}

/**
 * CommandPalette provides quick command access via fuzzy search.
 *
 * Features:
 * - Fuzzy search through available commands
 * - Keyboard navigation (Arrow keys, Enter, Escape)
 * - Grouped commands by category
 * - Accessible with proper ARIA attributes
 * - Focus trapping within the dialog
 */
export function CommandPalette({
  commands,
  isOpen,
  onClose,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();
  const inputId = useId();

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) {
      return commands;
    }
    return commands.filter((cmd) => fuzzyMatch(query, cmd.label));
  }, [commands, query]);

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups = new Map<string, Command[]>();
    for (const cmd of filteredCommands) {
      const existing = groups.get(cmd.category) || [];
      existing.push(cmd);
      groups.set(cmd.category, existing);
    }
    return groups;
  }, [filteredCommands]);

  // Flatten for index-based navigation
  const flatCommands = useMemo(() => {
    return Array.from(groupedCommands.values()).flat();
  }, [groupedCommands]);

  // Reset state when opened/closed
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(-1);
      setHighlightedIndex(-1);
      // Focus input immediately
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Reset selection when filtered results change
  useEffect(() => {
    setSelectedIndex(-1);
    setHighlightedIndex(-1);
  }, [query]);

  const executeCommand = useCallback(
    (command: Command) => {
      command.action();
      onClose();
    },
    [onClose],
  );

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLInputElement>) => {
      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          setSelectedIndex((prev) => {
            const next = prev + 1;
            return next >= flatCommands.length ? 0 : next;
          });
          break;
        case "ArrowUp":
          event.preventDefault();
          setSelectedIndex((prev) => {
            const next = prev - 1;
            return next < 0 ? flatCommands.length - 1 : next;
          });
          break;
        case "Enter":
          event.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < flatCommands.length) {
            executeCommand(flatCommands[selectedIndex]);
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
    [flatCommands, selectedIndex, executeCommand, onClose],
  );

  const handleItemClick = useCallback(
    (command: Command) => {
      executeCommand(command);
    },
    [executeCommand],
  );

  const handleItemHover = useCallback((index: number) => {
    setHighlightedIndex(index);
  }, []);

  const handleBackdropClick = useCallback(() => {
    onClose();
  }, [onClose]);

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

  if (!isOpen) {
    return null;
  }

  // Calculate active descendant
  const activeIndex = selectedIndex >= 0 ? selectedIndex : highlightedIndex;
  const activeDescendant =
    activeIndex >= 0 ? `command-option-${flatCommands[activeIndex]?.id}` : undefined;

  // Track running index for option IDs
  let runningIndex = 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50"
        data-testid="command-palette-backdrop"
        onClick={handleBackdropClick}
      />

      {/* Dialog */}
      <div
        aria-label="Command palette"
        className="fixed left-1/2 top-1/4 z-50 w-full max-w-lg -translate-x-1/2 transform rounded-lg bg-white shadow-xl"
        role="dialog"
      >
        {/* Search input */}
        <div className="border-b p-4">
          <input
            aria-activedescendant={activeDescendant}
            aria-autocomplete="list"
            aria-controls={listboxId}
            aria-expanded="true"
            autoComplete="off"
            autoFocus
            className="w-full rounded-md border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            id={inputId}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search commands..."
            ref={inputRef}
            role="combobox"
            type="text"
            value={query}
          />
        </div>

        {/* Command list */}
        <div className="max-h-80 overflow-y-auto p-2">
          {flatCommands.length === 0 ? (
            <div className="px-3 py-4 text-center text-sm text-gray-500">
              No commands found
            </div>
          ) : (
            <ul id={listboxId} role="listbox">
              {Array.from(groupedCommands.entries()).map(
                ([category, categoryCommands]) => (
                  <li key={category}>
                    {/* Category header */}
                    <div className="px-3 py-1 text-xs font-semibold uppercase text-gray-500">
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </div>

                    {/* Category commands */}
                    <ul>
                      {categoryCommands.map((command) => {
                        const itemIndex = runningIndex++;
                        const isSelected = selectedIndex === itemIndex;
                        const isHighlighted =
                          highlightedIndex === itemIndex && selectedIndex < 0;

                        return (
                          <li
                            aria-selected={isSelected}
                            className={`flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-sm ${
                              isSelected
                                ? "bg-blue-100 text-blue-900"
                                : isHighlighted
                                  ? "bg-gray-100"
                                  : "text-gray-700 hover:bg-gray-100"
                            }`}
                            data-highlighted={isHighlighted || undefined}
                            id={`command-option-${command.id}`}
                            key={command.id}
                            onClick={() => handleItemClick(command)}
                            onMouseEnter={() => handleItemHover(itemIndex)}
                            role="option"
                          >
                            <span>{command.label}</span>
                            {command.shortcut && (
                              <kbd className="rounded bg-gray-200 px-1.5 py-0.5 font-mono text-xs text-gray-600">
                                {command.shortcut}
                              </kbd>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </li>
                ),
              )}
            </ul>
          )}
        </div>
      </div>
    </>
  );
}
