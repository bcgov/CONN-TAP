import { describe, expect, it } from "vitest";

import { fmtMillions, fmtMillionsFixed } from "./format-utils";

describe("fmtMillions", () => {
  it("formats whole millions without decimals", () => {
    expect(fmtMillions(2)).toBe("$2M");
  });

  it("formats fractional millions", () => {
    expect(fmtMillions(2.5)).toBe("$2.5M");
  });
});

describe("fmtMillionsFixed", () => {
  it("always shows one decimal place", () => {
    expect(fmtMillionsFixed(2)).toBe("$2.0M");
    expect(fmtMillionsFixed(2.56)).toBe("$2.6M");
  });
});
