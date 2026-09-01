import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createRef } from "react";
import {
  ChartDownloadButton,
  type CsvData,
  type ExportFormat,
} from "@/components/chart-download-button";

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

const renderButton = (
  title = "My Chart",
  label?: string,
  extra?: { formats?: ExportFormat[]; csvData?: CsvData },
) => {
  const ref = createRef<HTMLElement | null>();
  render(
    <div>
      <div ref={ref as React.RefObject<HTMLDivElement>}>Chart content</div>
      <ChartDownloadButton
        targetRef={ref}
        title={title}
        {...(label ? { label } : {})}
        {...extra}
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

  it("only offers the formats passed via the formats prop", async () => {
    const user = userEvent.setup();
    renderButton("My Chart", undefined, { formats: ["png"] });

    await user.click(screen.getByRole("button", { name: "Download chart" }));

    expect(screen.getByRole("menuitem", { name: "PNG" })).toBeInTheDocument();
    expect(
      screen.queryByRole("menuitem", { name: "JPEG" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("menuitem", { name: "PDF" }),
    ).not.toBeInTheDocument();
  });

  it("renders menu items in the order given by the formats prop", async () => {
    const user = userEvent.setup();
    const csvData: CsvData = { headers: ["Name"], rows: [["BGE"]] };
    renderButton("My Chart", undefined, {
      formats: ["xls", "csv", "png", "jpeg", "pdf"],
      csvData,
    });

    await user.click(screen.getByRole("button", { name: "Download chart" }));

    const labels = screen
      .getAllByRole("menuitem")
      .map((item) => item.textContent);
    expect(labels).toEqual(["XLS", "CSV", "PNG", "JPEG", "PDF"]);
  });

  it("does not offer CSV or XLS when no csvData is passed", async () => {
    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button", { name: "Download chart" }));

    expect(
      screen.queryByRole("menuitem", { name: "CSV" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("menuitem", { name: "XLS" }),
    ).not.toBeInTheDocument();
  });

  it("offers CSV once csvData is passed and downloads it via a blob URL", async () => {
    const user = userEvent.setup();
    if (!URL.createObjectURL) URL.createObjectURL = vi.fn();
    if (!URL.revokeObjectURL) URL.revokeObjectURL = vi.fn();
    const createObjectURL = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:fake-url");
    const revokeObjectURL = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => {});
    const csvData: CsvData = {
      headers: ["Name", "Spend"],
      rows: [["BGE, One", 100]],
    };

    renderButton("My Chart", undefined, { csvData });

    await user.click(screen.getByRole("button", { name: "Download chart" }));
    expect(screen.getByRole("menuitem", { name: "CSV" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "XLS" })).toBeInTheDocument();

    await user.click(screen.getByRole("menuitem", { name: "CSV" }));

    await waitFor(() => expect(createObjectURL).toHaveBeenCalled());
    const blob = createObjectURL.mock.calls[0][0] as Blob;
    expect(blob.type).toBe("text/csv;charset=utf-8;");
    const text = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsText(blob);
    });
    expect(text).toBe('Name,Spend\n"BGE, One",100');
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");
  });

  it("downloads XLS as a real .xlsx workbook", async () => {
    const user = userEvent.setup();
    if (!URL.createObjectURL) URL.createObjectURL = vi.fn();
    if (!URL.revokeObjectURL) URL.revokeObjectURL = vi.fn();
    const createObjectURL = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:fake-url");
    const csvData: CsvData = {
      headers: ["Name", "Spend"],
      rows: [["BGE One", 100]],
    };

    renderButton("My Chart", undefined, { csvData });

    await user.click(screen.getByRole("button", { name: "Download chart" }));
    await user.click(screen.getByRole("menuitem", { name: "XLS" }));

    await waitFor(() => expect(createObjectURL).toHaveBeenCalled());
    const blob = createObjectURL.mock.calls[0][0] as Blob;
    expect(blob.type).toBe(
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    );
    // A real xlsx is a zip archive, which starts with the "PK" signature —
    // proof this isn't just CSV text mislabeled with an Excel MIME type.
    const buffer = await new Promise<ArrayBuffer>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as ArrayBuffer);
      reader.readAsArrayBuffer(blob);
    });
    const bytes = new Uint8Array(buffer);
    expect(bytes[0]).toBe(0x50); // "P"
    expect(bytes[1]).toBe(0x4b); // "K"
  });

  it("respects an explicit formats prop that omits csv, even if csvData is present", async () => {
    const user = userEvent.setup();
    const csvData: CsvData = { headers: ["Name"], rows: [["BGE"]] };
    renderButton("My Chart", undefined, { formats: ["png"], csvData });

    await user.click(screen.getByRole("button", { name: "Download chart" }));

    expect(
      screen.queryByRole("menuitem", { name: "CSV" }),
    ).not.toBeInTheDocument();
  });
});
