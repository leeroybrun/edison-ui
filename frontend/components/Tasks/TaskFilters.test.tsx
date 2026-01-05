import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TaskFilters } from "./TaskFilters";
import type { Session, TaskFilters as TaskFiltersType } from "./types";

const mockSessions: Session[] = [
  { sessionId: "session-1", name: "Feature Sprint" },
  { sessionId: "session-2", name: "Bug Fixes" },
];

describe("TaskFilters", () => {
  it("renders search input", () => {
    render(
      <TaskFilters filters={{}} sessions={[]} onFiltersChange={() => {}} />,
    );

    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
  });

  it("renders state filter dropdown", () => {
    render(
      <TaskFilters filters={{}} sessions={[]} onFiltersChange={() => {}} />,
    );

    expect(screen.getByLabelText(/state/i)).toBeInTheDocument();
  });

  it("renders session filter dropdown when sessions provided", () => {
    render(
      <TaskFilters
        filters={{}}
        sessions={mockSessions}
        onFiltersChange={() => {}}
      />,
    );

    expect(screen.getByLabelText(/session/i)).toBeInTheDocument();
  });

  it("calls onFiltersChange when search input changes", () => {
    const handleChange = vi.fn();
    render(
      <TaskFilters filters={{}} sessions={[]} onFiltersChange={handleChange} />,
    );

    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: "login" } });

    expect(handleChange).toHaveBeenCalledWith({ search: "login" });
  });

  it("calls onFiltersChange when state filter changes", () => {
    const handleChange = vi.fn();
    render(
      <TaskFilters filters={{}} sessions={[]} onFiltersChange={handleChange} />,
    );

    const select = screen.getByLabelText(/state/i);
    fireEvent.change(select, { target: { value: "wip" } });

    expect(handleChange).toHaveBeenCalledWith({ state: "wip" });
  });

  it("calls onFiltersChange when session filter changes", () => {
    const handleChange = vi.fn();
    render(
      <TaskFilters
        filters={{}}
        sessions={mockSessions}
        onFiltersChange={handleChange}
      />,
    );

    const select = screen.getByLabelText(/session/i);
    fireEvent.change(select, { target: { value: "session-1" } });

    expect(handleChange).toHaveBeenCalledWith({ sessionId: "session-1" });
  });

  it("displays current filter values", () => {
    const filters: TaskFiltersType = {
      search: "test query",
      state: "done",
      sessionId: "session-2",
    };

    render(
      <TaskFilters
        filters={filters}
        sessions={mockSessions}
        onFiltersChange={() => {}}
      />,
    );

    const searchInput = screen.getByPlaceholderText(/search/i);
    expect(searchInput).toHaveValue("test query");

    const stateSelect = screen.getByLabelText(/state/i);
    expect(stateSelect).toHaveValue("done");

    const sessionSelect = screen.getByLabelText(/session/i);
    expect(sessionSelect).toHaveValue("session-2");
  });

  it("has accessible labels for all controls", () => {
    render(
      <TaskFilters
        filters={{}}
        sessions={mockSessions}
        onFiltersChange={() => {}}
      />,
    );

    expect(screen.getByLabelText(/search/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/state/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/session/i)).toBeInTheDocument();
  });

  it("clears filter when 'All' option selected", () => {
    const handleChange = vi.fn();
    render(
      <TaskFilters
        filters={{ state: "done" }}
        sessions={[]}
        onFiltersChange={handleChange}
      />,
    );

    const select = screen.getByLabelText(/state/i);
    fireEvent.change(select, { target: { value: "" } });

    expect(handleChange).toHaveBeenCalledWith({ state: undefined });
  });

  it("renders session filter with Unscoped option even without sessions", () => {
    render(
      <TaskFilters filters={{}} sessions={[]} onFiltersChange={() => {}} />,
    );

    const select = screen.getByLabelText(/session/i);
    expect(select).toBeInTheDocument();
    expect(screen.getByText("Unscoped (no session)")).toBeInTheDocument();
  });

  it("calls onFiltersChange with 'none' when Unscoped option selected", () => {
    const handleChange = vi.fn();
    render(
      <TaskFilters
        filters={{}}
        sessions={mockSessions}
        onFiltersChange={handleChange}
      />,
    );

    const select = screen.getByLabelText(/session/i);
    fireEvent.change(select, { target: { value: "none" } });

    expect(handleChange).toHaveBeenCalledWith({ sessionId: "none" });
  });
});
