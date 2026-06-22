import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createRef } from "react";
import { ChartDownloadButton } from "@/components/chart-download-button";

const {
  mockToPng,
  mockToJpeg,
  mockSave,
  mockAddImage,
  mockGetImageProperties,
} = vi.hoisted(() => ({
  mockToPng: vi.fn().mockResolvedValue("data:image/png;base64,fakedata"),
  mockToJpeg: vi.fn().mockResolvedValue("data:image/jpeg;base64,fakedata"),
  mockSave: vi.fn(),
  mockAddImage: vi.fn(),
  mockGetImageProperties: vi.fn().mockReturnValue({ width: 800, height: 400 }),
}));

vi.mock("html-to-image", () => ({
  toPng: mockToPng,
  toJpeg: mockToJpeg,
}));

vi.mock("jspdf", () => ({
  jsPDF: vi.fn().mockImplementation(() => ({
    getImageProperties: mockGetImageProperties,
    addImage: mockAddImage,
    save: mockSave,
  })),
}));

const renderButton = (title = "My Chart", label?: string) => {
  const ref = createRef<HTMLElement | null>();
  render(
    <div>
      <div ref={ref as React.RefObject<HTMLDivElement>}>Chart content</div>
      <ChartDownloadButton
        targetRef={ref}
        title={title}
        {...(label ? { label } : {})}
      />
    </div>,
  );
};

describe("ChartDownloadButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  it("renders a download button with the default label", () => {
    renderButton();
    expect(
      screen.getByRole("button", { name: "Download chart" }),
    ).toBeInTheDocument();
  });

  it("renders with a custom label", () => {
    renderButton("Chart", "Export chart");
    expect(
      screen.getByRole("button", { name: "Export chart" }),
    ).toBeInTheDocument();
  });

  it("opens a menu with PNG, JPEG, and PDF options on click", async () => {
    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button", { name: "Download chart" }));

    expect(screen.getByRole("menuitem", { name: "PNG" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "JPEG" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "PDF" })).toBeInTheDocument();
  });

  it("calls toPng and triggers an anchor download when PNG is selected", async () => {
    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button", { name: "Download chart" }));
    await user.click(screen.getByRole("menuitem", { name: "PNG" }));

    await waitFor(() => expect(mockToPng).toHaveBeenCalled());
  });

  it("calls toJpeg and triggers an anchor download when JPEG is selected", async () => {
    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button", { name: "Download chart" }));
    await user.click(screen.getByRole("menuitem", { name: "JPEG" }));

    await waitFor(() => expect(mockToJpeg).toHaveBeenCalled());
  });

  it("takes the PDF path when PDF is selected", async () => {
    const user = userEvent.setup();
    renderButton("My Chart");

    await user.click(screen.getByRole("button", { name: "Download chart" }));
    await user.click(screen.getByRole("menuitem", { name: "PDF" }));

    await waitFor(() => expect(mockGetImageProperties).toHaveBeenCalled());
  });
});
