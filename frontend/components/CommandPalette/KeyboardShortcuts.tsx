"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";

import type { ViewMode } from "../Tasks/types";

/**
 * Shortcut handler function
 */
type ShortcutHandler = () => void;

/**
 * Context value for keyboard shortcuts
 */
interface KeyboardShortcutsContextValue {
  /** Register a keyboard shortcut */
  register: (shortcut: string, handler: ShortcutHandler) => () => void;
  /** Whether the command palette is open */
  isCommandPaletteOpen: boolean;
  /** Open the command palette */
  openCommandPalette: () => void;
  /** Close the command palette */
  closeCommandPalette: () => void;
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextValue | null>(
  null,
);

/**
 * Command palette context value
 */
interface CommandPaletteContextValue {
  isOpen: boolean;
  open: () => void;
  close: () => void;
}

const CommandPaletteContext = createContext<CommandPaletteContextValue | null>(null);

export interface KeyboardShortcutsProviderProps {
  children: ReactNode;
  /** Callback when view mode should change */
  onViewChange?: (view: ViewMode) => void;
}

/**
 * Check if the target is an input element
 */
function isInputElement(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false;

  const tagName = target.tagName.toLowerCase();
  if (tagName === "input" || tagName === "textarea" || tagName === "select") {
    return true;
  }

  // Check contenteditable - check both the property and attribute
  if (target.isContentEditable) {
    return true;
  }

  // Also check for contenteditable attribute directly (for jsdom compatibility)
  const contentEditableAttr = target.getAttribute("contenteditable");
  if (contentEditableAttr === "true" || contentEditableAttr === "") {
    return true;
  }

  return false;
}

/**
 * Sequence timeout in milliseconds
 */
const SEQUENCE_TIMEOUT = 1000;

/**
 * KeyboardShortcutsProvider manages global keyboard shortcuts.
 *
 * Features:
 * - Cmd/Ctrl+K: Open command palette
 * - g t: Go to tasks
 * - g s: Go to sessions
 * - 1/2/3: Switch view modes
 * - /: Focus search
 * - Custom shortcut registration
 */
export function KeyboardShortcutsProvider({
  children,
  onViewChange,
}: KeyboardShortcutsProviderProps) {
  const router = useRouter();
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [sequence, setSequence] = useState("");
  const sequenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const handlersRef = useRef<Map<string, ShortcutHandler>>(new Map());

  // Register a shortcut handler
  const register = useCallback(
    (shortcut: string, handler: ShortcutHandler): (() => void) => {
      handlersRef.current.set(shortcut, handler);
      return () => {
        handlersRef.current.delete(shortcut);
      };
    },
    [],
  );

  const openCommandPalette = useCallback(() => {
    setIsCommandPaletteOpen(true);
  }, []);

  const closeCommandPalette = useCallback(() => {
    setIsCommandPaletteOpen(false);
  }, []);

  // Handle sequence reset
  const resetSequence = useCallback(() => {
    setSequence("");
    if (sequenceTimeoutRef.current) {
      clearTimeout(sequenceTimeoutRef.current);
      sequenceTimeoutRef.current = null;
    }
  }, []);

  // Handle global keydown
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl+K always works, even in inputs
      if ((event.metaKey || event.ctrlKey) && event.key === "k") {
        event.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
        resetSequence();
        return;
      }

      // If command palette is open, don't process other shortcuts
      if (isCommandPaletteOpen) {
        return;
      }

      // Skip other shortcuts in input elements
      if (isInputElement(event.target)) {
        return;
      }

      // Handle single-key shortcuts
      const key = event.key.toLowerCase();

      // View switching (1, 2, 3)
      if (key === "1" && onViewChange) {
        event.preventDefault();
        onViewChange("list");
        resetSequence();
        return;
      }
      if (key === "2" && onViewChange) {
        event.preventDefault();
        onViewChange("board");
        resetSequence();
        return;
      }
      if (key === "3" && onViewChange) {
        event.preventDefault();
        onViewChange("tree");
        resetSequence();
        return;
      }

      // Focus search with /
      if (key === "/") {
        event.preventDefault();
        const searchInput = document.getElementById("search-input");
        if (searchInput) {
          searchInput.focus();
        }
        resetSequence();
        return;
      }

      // Check custom handlers for single keys
      const handler = handlersRef.current.get(key);
      if (handler) {
        event.preventDefault();
        handler();
        resetSequence();
        return;
      }

      // Build sequence for multi-key shortcuts
      const newSequence = sequence + key;

      // Clear existing timeout
      if (sequenceTimeoutRef.current) {
        clearTimeout(sequenceTimeoutRef.current);
      }

      // Check for sequence shortcuts
      if (newSequence === "gt") {
        event.preventDefault();
        router.push("/projects/default/tasks");
        resetSequence();
        return;
      }
      if (newSequence === "gs") {
        event.preventDefault();
        router.push("/projects/default/sessions");
        resetSequence();
        return;
      }

      // Check custom handlers for sequences
      const sequenceHandler = handlersRef.current.get(newSequence);
      if (sequenceHandler) {
        event.preventDefault();
        sequenceHandler();
        resetSequence();
        return;
      }

      // Update sequence with timeout
      if (key.length === 1 && /[a-z]/.test(key)) {
        setSequence(newSequence);
        sequenceTimeoutRef.current = setTimeout(() => {
          setSequence("");
        }, SEQUENCE_TIMEOUT);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      if (sequenceTimeoutRef.current) {
        clearTimeout(sequenceTimeoutRef.current);
      }
    };
  }, [sequence, isCommandPaletteOpen, onViewChange, router, resetSequence]);

  const shortcutsValue = useMemo<KeyboardShortcutsContextValue>(
    () => ({
      register,
      isCommandPaletteOpen,
      openCommandPalette,
      closeCommandPalette,
    }),
    [register, isCommandPaletteOpen, openCommandPalette, closeCommandPalette],
  );

  const paletteValue = useMemo<CommandPaletteContextValue>(
    () => ({
      isOpen: isCommandPaletteOpen,
      open: openCommandPalette,
      close: closeCommandPalette,
    }),
    [isCommandPaletteOpen, openCommandPalette, closeCommandPalette],
  );

  return (
    <KeyboardShortcutsContext.Provider value={shortcutsValue}>
      <CommandPaletteContext.Provider value={paletteValue}>
        {children}
      </CommandPaletteContext.Provider>
    </KeyboardShortcutsContext.Provider>
  );
}

/**
 * Hook to register a keyboard shortcut
 */
export function useKeyboardShortcuts(
  shortcut: string,
  handler: ShortcutHandler,
): void {
  const context = useContext(KeyboardShortcutsContext);

  useEffect(() => {
    if (!context) return;
    return context.register(shortcut, handler);
  }, [context, shortcut, handler]);
}

/**
 * Hook to access the command palette state
 */
export function useCommandPalette(): CommandPaletteContextValue {
  const context = useContext(CommandPaletteContext);
  if (!context) {
    throw new Error("useCommandPalette must be used within KeyboardShortcutsProvider");
  }
  return context;
}

/**
 * Hook to access keyboard shortcuts context
 */
export function useKeyboardShortcutsContext(): KeyboardShortcutsContextValue {
  const context = useContext(KeyboardShortcutsContext);
  if (!context) {
    throw new Error(
      "useKeyboardShortcutsContext must be used within KeyboardShortcutsProvider",
    );
  }
  return context;
}
