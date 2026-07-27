import { fireEvent, render, screen } from "@testing-library/react";

import { ConfidentialityBanner } from "@/components/confidentiality-banner";

describe("ConfidentialityBanner", () => {
  it("renders the confidentiality alert with title and body", () => {
    render(<ConfidentialityBanner />);

    expect(screen.getByText("Confidentiality Alert")).toBeInTheDocument();
    expect(
      screen.getByText(/authorized BGE and Administrator/i),
    ).toBeInTheDocument();
  });

  it("collapses when the BC Gov close button is clicked", () => {
    const { container } = render(<ConfidentialityBanner />);
    const collapse = container.firstElementChild as HTMLElement;

    expect(collapse).toHaveAttribute("data-dismissed", "false");

    fireEvent.click(screen.getByRole("button", { name: "Close this alert" }));

    expect(collapse).toHaveAttribute("data-dismissed", "true");
  });
});
