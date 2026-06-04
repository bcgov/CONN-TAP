export type YearType = "fiscal" | "calendar";

export function periodsToYearsQuarters(periods: string[]): { years: string[]; quarters: string[] } {
  const yearSet = new Set<string>();
  const quarterSet = new Set<string>();
  for (const p of periods) {
    const [year, quarter] = p.split("_");
    yearSet.add(year);
    quarterSet.add(quarter);
  }
  return {
    years: Array.from(yearSet).sort(),
    quarters: Array.from(quarterSet).sort(),
  };
}

export function buildPeriodRangeLabel(periods: string[], yearType: YearType = "fiscal"): string {
  if (periods.length === 0) return "";
  const toLabel = (p: string) => {
    const [year, quarter] = p.split("_");
    return yearType === "fiscal" ? `Q${quarter} FY${year}` : `Q${quarter} ${year}`;
  };
  const first = periods[0];
  const last = periods[periods.length - 1];
  if (first === last) return `(${toLabel(first)})`;
  return `(${toLabel(first)} – ${toLabel(last)})`;
}
