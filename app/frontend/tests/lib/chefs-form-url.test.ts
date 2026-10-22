import { describe, expect, it } from "vitest";
import { parseChefsFormUrl } from "@/lib/chefs-form-url";

describe("parseChefsFormUrl", () => {
  it("accepts https URLs", () => {
    expect(parseChefsFormUrl("https://submit.digital.gov.bc.ca/app/form/submit?f=abc")).toBe(
      "https://submit.digital.gov.bc.ca/app/form/submit?f=abc",
    );
  });

  it.each([undefined, "", "not a url", "http://example.com", "javascript:alert(1)"])(
    "rejects %s",
    (value) => {
      expect(parseChefsFormUrl(value)).toBeNull();
    },
  );
});
