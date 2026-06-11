import { render, screen } from "@testing-library/react";

import { MinimalFooter } from "@/components/minimal-footer";

describe("MinimalFooter", () => {
  it("renders footer navigation links", () => {
    render(<MinimalFooter />);

    expect(screen.getByRole("navigation", { name: "Footer links" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute(
      "href",
      "https://www2.gov.bc.ca/gov/content/home",
    );
    expect(screen.getByRole("link", { name: "Privacy" })).toBeInTheDocument();
  });
});
