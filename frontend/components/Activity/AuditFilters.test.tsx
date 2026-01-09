import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuditFilters } from "./AuditFilters";
import type { AuditFiltersState, Session, TaskRef } from "./types";

const mockSessions: Session[] = [
  { sessionId: "session-1", name: "Feature implementation" },
  { sessionId: "session-2", name: "Bug fixes" },
];

const mockTasks: TaskRef[] = [
  { taskId: "T001", title: "Implement login" },
  { taskId: "T002", title: "Add authentication" },
];

const defaultFilters: AuditFiltersState = {
  sessionId: undefined,
  taskId: undefined,
  eventType: undefined,
  since: undefined,
};

describe("AuditFilters", () => {
  it("renders all filter controls", () => {
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    expect(screen.getByLabelText(/session/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/task/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/event type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/since|date/i)).toBeInTheDocument();
  });

  it("displays session options in dropdown", () => {
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const sessionSelect = screen.getByLabelText(/session/i);
    expect(sessionSelect).toBeInTheDocument();

    // Options should include sessions
    expect(
      screen.getByRole("option", { name: /Feature implementation/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Bug fixes/i }),
    ).toBeInTheDocument();
  });

  it("displays task options in dropdown", () => {
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const taskSelect = screen.getByLabelText(/task/i);
    expect(taskSelect).toBeInTheDocument();

    // Options should include tasks
    expect(
      screen.getByRole("option", { name: /T001.*Implement login/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /T002.*Add authentication/i }),
    ).toBeInTheDocument();
  });

  it("calls onChange when session filter changes", () => {
    const onChange = vi.fn();
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={onChange}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const sessionSelect = screen.getByLabelText(/session/i);
    fireEvent.change(sessionSelect, { target: { value: "session-1" } });

    expect(onChange).toHaveBeenCalledWith({ sessionId: "session-1" });
  });

  it("calls onChange when task filter changes", () => {
    const onChange = vi.fn();
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={onChange}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const taskSelect = screen.getByLabelText(/task/i);
    fireEvent.change(taskSelect, { target: { value: "T001" } });

    expect(onChange).toHaveBeenCalledWith({ taskId: "T001" });
  });

  it("calls onChange when event type filter changes", () => {
    const onChange = vi.fn();
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={onChange}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const eventTypeSelect = screen.getByLabelText(/event type/i);
    fireEvent.change(eventTypeSelect, { target: { value: "task.transition" } });

    expect(onChange).toHaveBeenCalledWith({ eventType: "task.transition" });
  });

  it("calls onChange when since date changes", () => {
    const onChange = vi.fn();
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={onChange}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const dateInput = screen.getByLabelText(/since|date/i);
    fireEvent.change(dateInput, { target: { value: "2025-12-01" } });

    expect(onChange).toHaveBeenCalledWith({ since: "2025-12-01" });
  });

  it("displays current filter values", () => {
    const currentFilters: AuditFiltersState = {
      sessionId: "session-1",
      taskId: "T001",
      eventType: "task.transition",
      since: "2025-12-01",
    };

    render(
      <AuditFilters
        filters={currentFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    expect(screen.getByLabelText(/session/i)).toHaveValue("session-1");
    expect(screen.getByLabelText(/task/i)).toHaveValue("T001");
    expect(screen.getByLabelText(/event type/i)).toHaveValue("task.transition");
    expect(screen.getByLabelText(/since|date/i)).toHaveValue("2025-12-01");
  });

  it("shows All sessions option", () => {
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    expect(
      screen.getByRole("option", { name: /all sessions/i }),
    ).toBeInTheDocument();
  });

  it("shows All tasks option", () => {
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    expect(
      screen.getByRole("option", { name: /all tasks/i }),
    ).toBeInTheDocument();
  });

  it("shows common event types in dropdown", () => {
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const eventTypeSelect = screen.getByLabelText(/event type/i);
    expect(eventTypeSelect).toBeInTheDocument();

    // Common event types
    expect(
      screen.getByRole("option", { name: /all event types/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /task\.transition/i }),
    ).toBeInTheDocument();
  });

  it("uses provided eventTypes override list when set", () => {
    render(
      <AuditFilters
        eventTypes={["session.create", "task.claim"]}
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    expect(
      screen.getByRole("option", { name: "session.create" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "task.claim" })).toBeInTheDocument();
  });

  it("has accessible labels for all controls", () => {
    render(
      <AuditFilters
        filters={defaultFilters}
        onChange={() => {}}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    // All controls should have associated labels
    expect(screen.getByLabelText(/session/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/task/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/event type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/since|date/i)).toBeInTheDocument();
  });

  it("clears session filter when selecting All sessions", () => {
    const onChange = vi.fn();
    const currentFilters: AuditFiltersState = {
      sessionId: "session-1",
    };

    render(
      <AuditFilters
        filters={currentFilters}
        onChange={onChange}
        sessions={mockSessions}
        tasks={mockTasks}
      />,
    );

    const sessionSelect = screen.getByLabelText(/session/i);
    fireEvent.change(sessionSelect, { target: { value: "" } });

    expect(onChange).toHaveBeenCalledWith({ sessionId: undefined });
  });
});
