export type YearType = "fiscal" | "calendar";

export function currentFiscalYear(date = new Date()) {
  return date.getMonth() >= 3 ? date.getFullYear() + 1 : date.getFullYear();
}

export function buildYearOptions(yearType: YearType) {
  const currentYear = yearType === "fiscal" ? currentFiscalYear() : new Date().getFullYear();
  const endYear = Math.max(currentYear, 2027);
  const years = [];
  for (let year = 2024; year <= endYear; year += 1) {
    years.push(year);
  }
  return years;
}
