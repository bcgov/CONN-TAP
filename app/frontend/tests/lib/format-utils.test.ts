import { describe, expect, it } from "vitest";

import { fmtMillions, fmtMillionsFixed } from "@/lib/format-utils";

describe("fmtMillions", () => {
  it("formats whole millions without decimals", () => {
    expect(fmtMillions(2)).toBe("$2M");
  });

  it("formats fractional millions", () => {
    expect(fmtMillions(2.5)).toBe("$2.5M");
  });

  it("switches to the M suffix at exactly $1M", () => {
    expect(fmtMillions(1)).toBe("$1M");
    expect(fmtMillions(0.99)).toBe("$990,000");
  });

  // Below $1M the millions format hides the amount: "$0.08M" reads as nothing
  // when it's $80,000, and under $5,000 it collapsed to "$0M" entirely.
  it("shows whole dollars below $1M", () => {
    expect(fmtMillions(0.08)).toBe("$80,000");
    expect(fmtMillions(0.0812)).toBe("$81,200");
    expect(fmtMillions(0.004)).toBe("$4,000");
    expect(fmtMillions(0.0001)).toBe("$100");
  });

  it("groups thousands in the dollar fallback", () => {
    expect(fmtMillions(0.0049)).toBe("$4,900");
    expect(fmtMillions(0.5)).toBe("$500,000");
  });

  it("shows a bare $0 only for genuinely zero spend", () => {
    expect(fmtMillions(0)).toBe("$0");
  });

  it("keeps the sign on small negative amounts", () => {
    expect(fmtMillions(-0.004)).toBe("$-4,000");
  });
});

describe("fmtMillionsFixed", () => {
  it("always shows one decimal place", () => {
    expect(fmtMillionsFixed(2)).toBe("$2.0M");
    expect(fmtMillionsFixed(2.56)).toBe("$2.6M");
  });
});
