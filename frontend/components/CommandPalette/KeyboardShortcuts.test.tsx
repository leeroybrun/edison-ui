import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  KeyboardShortcutsProvider,
  useKeyboardShortcuts,
  useCommandPalette,
} from "./KeyboardShortcuts";

// Mock next/navigation
const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => "/projects/default",
}));

// Test component that uses the hooks
function TestConsumer() {
  const { isOpen, open, close } = useCommandPalette();
  return (
    <div>
      <span data-testid="is-open">{String(isOpen)}</span>
      <button onClick={open} type="button">
        Open
      </button>
      <button onClick={close} type="button">
        Close
      </button>
    </div>
  );
}

// Test component for shortcut registration
function ShortcutConsumer({
  shortcut,
  callback,
}: {
  shortcut: string;
  callback: () => void;
}) {
  useKeyboardShortcuts(shortcut, callback);
  return <div data-testid="shortcut-registered">Registered</div>;
}

describe("KeyboardShortcutsProvider", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Command Palette Toggle", () => {
    it("opens command palette with Cmd+K on Mac", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <TestConsumer />
        </KeyboardShortcutsProvider>,
      );

      expect(screen.getByTestId("is-open")).toHaveTextContent("false");

      await user.keyboard("{Meta>}k{/Meta}");

      expect(screen.getByTestId("is-open")).toHaveTextContent("true");
    });

    it("opens command palette with Ctrl+K on Windows/Linux", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <TestConsumer />
        </KeyboardShortcutsProvider>,
      );

      expect(screen.getByTestId("is-open")).toHaveTextContent("false");

      await user.keyboard("{Control>}k{/Control}");

      expect(screen.getByTestId("is-open")).toHaveTextContent("true");
    });

    it("closes command palette when already open", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <TestConsumer />
        </KeyboardShortcutsProvider>,
      );

      await user.click(screen.getByText("Open"));
      expect(screen.getByTestId("is-open")).toHaveTextContent("true");

      await user.keyboard("{Meta>}k{/Meta}");

      expect(screen.getByTestId("is-open")).toHaveTextContent("false");
    });
  });

  describe("Navigation Shortcuts", () => {
    it("navigates to tasks with g t sequence", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("gt");

      expect(mockPush).toHaveBeenCalledWith("/projects/default/tasks");
    });

    it("navigates to sessions with g s sequence", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("gs");

      expect(mockPush).toHaveBeenCalledWith("/projects/default/sessions");
    });
  });

  describe("View Shortcuts", () => {
    it("switches to list view with 1", async () => {
      const user = userEvent.setup();
      const onViewChange = vi.fn();
      render(
        <KeyboardShortcutsProvider onViewChange={onViewChange}>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("1");

      expect(onViewChange).toHaveBeenCalledWith("list");
    });

    it("switches to board view with 2", async () => {
      const user = userEvent.setup();
      const onViewChange = vi.fn();
      render(
        <KeyboardShortcutsProvider onViewChange={onViewChange}>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("2");

      expect(onViewChange).toHaveBeenCalledWith("board");
    });

    it("switches to tree view with 3", async () => {
      const user = userEvent.setup();
      const onViewChange = vi.fn();
      render(
        <KeyboardShortcutsProvider onViewChange={onViewChange}>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("3");

      expect(onViewChange).toHaveBeenCalledWith("tree");
    });
  });

  describe("Search Focus", () => {
    it("focuses search input with / key", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <input data-testid="search-input" id="task-search" type="text" />
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("/");

      // The provider should try to focus the search input
      // This test verifies the event is dispatched
      expect(document.activeElement).not.toBe(document.body);
    });
  });

  describe("Custom Shortcut Registration", () => {
    it("allows registering custom shortcuts", async () => {
      const user = userEvent.setup();
      const callback = vi.fn();

      render(
        <KeyboardShortcutsProvider>
          <ShortcutConsumer callback={callback} shortcut="x" />
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("x");

      expect(callback).toHaveBeenCalled();
    });

    it("unregisters shortcuts on unmount", async () => {
      const user = userEvent.setup();
      const callback = vi.fn();

      const { unmount } = render(
        <KeyboardShortcutsProvider>
          <ShortcutConsumer callback={callback} shortcut="x" />
        </KeyboardShortcutsProvider>,
      );

      unmount();

      render(
        <KeyboardShortcutsProvider>
          <div>Empty</div>
        </KeyboardShortcutsProvider>,
      );

      await user.keyboard("x");

      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe("Input Element Handling", () => {
    it("does not trigger shortcuts when typing in input", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <input data-testid="text-input" type="text" />
        </KeyboardShortcutsProvider>,
      );

      const input = screen.getByTestId("text-input");
      await user.click(input);
      await user.keyboard("gt");

      expect(mockPush).not.toHaveBeenCalled();
    });

    it("does not trigger shortcuts when typing in textarea", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <textarea data-testid="textarea" />
        </KeyboardShortcutsProvider>,
      );

      const textarea = screen.getByTestId("textarea");
      await user.click(textarea);
      await user.keyboard("gt");

      expect(mockPush).not.toHaveBeenCalled();
    });

    it("does not trigger shortcuts in contenteditable", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <div contentEditable="true" data-testid="editable" tabIndex={0}>
            Edit me
          </div>
        </KeyboardShortcutsProvider>,
      );

      const editable = screen.getByTestId("editable");
      editable.focus();
      await user.keyboard("gt");

      expect(mockPush).not.toHaveBeenCalled();
    });

    it("still triggers Cmd/Ctrl+K in inputs", async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsProvider>
          <TestConsumer />
          <input data-testid="text-input" type="text" />
        </KeyboardShortcutsProvider>,
      );

      const input = screen.getByTestId("text-input");
      await user.click(input);
      await user.keyboard("{Meta>}k{/Meta}");

      expect(screen.getByTestId("is-open")).toHaveTextContent("true");
    });
  });

  describe("Sequence Timeout", () => {
    it("completes sequence when keys are pressed quickly", async () => {
      // This test verifies that pressing 'g' then 't' quickly triggers navigation
      const user = userEvent.setup();

      render(
        <KeyboardShortcutsProvider>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      // Press 'g' then 't' in quick succession
      await user.keyboard("gt");

      expect(mockPush).toHaveBeenCalledWith("/projects/default/tasks");
    });

    it("builds sequence from consecutive keypresses", async () => {
      // This test verifies that the sequence builds correctly
      const user = userEvent.setup();

      render(
        <KeyboardShortcutsProvider>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      // Press 'g' then 's' for sessions
      await user.keyboard("gs");

      expect(mockPush).toHaveBeenCalledWith("/projects/default/sessions");
    });

    it("does not trigger on incomplete sequence", async () => {
      // This test verifies that pressing just 'g' doesn't trigger navigation
      const user = userEvent.setup();

      render(
        <KeyboardShortcutsProvider>
          <div>Test Content</div>
        </KeyboardShortcutsProvider>,
      );

      // Press only 'g' - should not trigger any navigation
      await user.keyboard("g");

      expect(mockPush).not.toHaveBeenCalled();
    });
  });
});
