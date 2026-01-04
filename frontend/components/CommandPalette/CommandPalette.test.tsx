import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { CommandPalette, type Command } from "./CommandPalette";

// Mock next/navigation
const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

const mockCommands: Command[] = [
  {
    id: "go-tasks",
    label: "Go to Tasks",
    shortcut: "g t",
    action: vi.fn(),
    category: "navigation",
  },
  {
    id: "go-sessions",
    label: "Go to Sessions",
    shortcut: "g s",
    action: vi.fn(),
    category: "navigation",
  },
  {
    id: "view-list",
    label: "Switch to List View",
    shortcut: "1",
    action: vi.fn(),
    category: "view",
  },
  {
    id: "view-board",
    label: "Switch to Board View",
    shortcut: "2",
    action: vi.fn(),
    category: "view",
  },
  {
    id: "view-tree",
    label: "Switch to Tree View",
    shortcut: "3",
    action: vi.fn(),
    category: "view",
  },
  {
    id: "open-task",
    label: "Open Task by ID",
    action: vi.fn(),
    category: "tasks",
  },
  {
    id: "filter-state",
    label: "Filter by State",
    action: vi.fn(),
    category: "filter",
  },
];

describe("CommandPalette", () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockCommands.forEach((cmd) => (cmd.action as ReturnType<typeof vi.fn>).mockClear());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Visibility", () => {
    it("is hidden by default when isOpen is false", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={false}
          onClose={vi.fn()}
        />,
      );

      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("renders as a dialog when isOpen is true", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByRole("dialog")).toHaveAttribute(
        "aria-label",
        "Command palette",
      );
    });

    it("renders a search input when open", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByRole("combobox")).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/search commands/i)).toBeInTheDocument();
    });
  });

  describe("Command List", () => {
    it("displays all commands when no search query", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByText("Go to Tasks")).toBeInTheDocument();
      expect(screen.getByText("Go to Sessions")).toBeInTheDocument();
      expect(screen.getByText("Switch to List View")).toBeInTheDocument();
    });

    it("displays command shortcuts when available", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByText("g t")).toBeInTheDocument();
      expect(screen.getByText("g s")).toBeInTheDocument();
    });

    it("groups commands by category", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByText("Navigation")).toBeInTheDocument();
      expect(screen.getByText("View")).toBeInTheDocument();
    });
  });

  describe("Fuzzy Search", () => {
    it("filters commands based on search query", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.type(searchInput, "task");

      await waitFor(() => {
        expect(screen.getByText("Go to Tasks")).toBeInTheDocument();
        expect(screen.getByText("Open Task by ID")).toBeInTheDocument();
        expect(screen.queryByText("Go to Sessions")).not.toBeInTheDocument();
      });
    });

    it("matches on partial words (fuzzy)", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.type(searchInput, "lst");

      await waitFor(() => {
        expect(screen.getByText("Switch to List View")).toBeInTheDocument();
      });
    });

    it("shows empty state when no matches", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.type(searchInput, "zzzznonexistent");

      await waitFor(() => {
        expect(screen.getByText(/no commands found/i)).toBeInTheDocument();
      });
    });
  });

  describe("Keyboard Navigation", () => {
    it("navigates to next item with ArrowDown", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.click(searchInput);
      await user.keyboard("{ArrowDown}");

      const options = screen.getAllByRole("option");
      expect(options[0]).toHaveAttribute("aria-selected", "true");
    });

    it("navigates to previous item with ArrowUp", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.click(searchInput);
      await user.keyboard("{ArrowDown}{ArrowDown}{ArrowUp}");

      const options = screen.getAllByRole("option");
      expect(options[0]).toHaveAttribute("aria-selected", "true");
    });

    it("wraps navigation at the end of list", async () => {
      const user = userEvent.setup();
      const shortCommands: Command[] = [
        { id: "cmd1", label: "Command 1", action: vi.fn(), category: "test" },
        { id: "cmd2", label: "Command 2", action: vi.fn(), category: "test" },
      ];

      render(
        <CommandPalette
          commands={shortCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.click(searchInput);
      await user.keyboard("{ArrowDown}{ArrowDown}{ArrowDown}");

      const options = screen.getAllByRole("option");
      expect(options[0]).toHaveAttribute("aria-selected", "true");
    });

    it("executes selected command on Enter", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={onClose}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.click(searchInput);
      await user.keyboard("{ArrowDown}{Enter}");

      expect(mockCommands[0].action).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });

    it("closes on Escape key", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={onClose}
        />,
      );

      await user.keyboard("{Escape}");

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe("Mouse Interaction", () => {
    it("executes command on click", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={onClose}
        />,
      );

      const taskOption = screen.getByText("Go to Tasks");
      await user.click(taskOption);

      expect(mockCommands[0].action).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });

    it("highlights command on hover", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const taskOption = screen.getByText("Go to Tasks").closest('[role="option"]');
      await user.hover(taskOption!);

      expect(taskOption).toHaveAttribute("data-highlighted", "true");
    });

    it("closes when clicking backdrop", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={onClose}
        />,
      );

      const backdrop = screen.getByTestId("command-palette-backdrop");
      await user.click(backdrop);

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("has proper ARIA attributes on listbox", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    it("combobox has aria-controls pointing to listbox", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const combobox = screen.getByRole("combobox");
      const listbox = screen.getByRole("listbox");
      expect(combobox).toHaveAttribute("aria-controls", listbox.id);
    });

    it("updates aria-activedescendant when navigating", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      await user.click(searchInput);
      await user.keyboard("{ArrowDown}");

      const options = screen.getAllByRole("option");
      expect(searchInput).toHaveAttribute("aria-activedescendant", options[0].id);
    });

    it("traps focus within the dialog", async () => {
      const user = userEvent.setup();
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      expect(document.activeElement).toBe(searchInput);

      await user.tab();
      expect(document.activeElement).toBe(searchInput);
    });
  });

  describe("Focus Management", () => {
    it("focuses search input when opened", () => {
      render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByRole("combobox")).toHaveFocus();
    });

    it("clears search query when closed", () => {
      const { rerender } = render(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      const searchInput = screen.getByRole("combobox");
      fireEvent.change(searchInput, { target: { value: "test" } });

      rerender(
        <CommandPalette
          commands={mockCommands}
          isOpen={false}
          onClose={vi.fn()}
        />,
      );

      rerender(
        <CommandPalette
          commands={mockCommands}
          isOpen={true}
          onClose={vi.fn()}
        />,
      );

      expect(screen.getByRole("combobox")).toHaveValue("");
    });
  });
});
