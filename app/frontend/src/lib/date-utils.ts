export type YearType = "fiscal" | "calendar";

export function currentFiscalYear(date = new Date()) {
  return date.getMonth() >= 3 ? date.getFullYear() + 1 : date.getFullYear();
}

const FISCAL_Q_START = ["Apr", "Jul", "Oct", "Jan"];
const FISCAL_Q_END = ["Jun", "Sep", "Dec", "Mar"];

export function buildDateRangeLabel(
  yearType: YearType,
  year: number,
  quarter: string,
): string {
  if (yearType === "fiscal") {
    if (quarter === "all") return `(Apr ${year - 1} – Mar ${year})`;
    const q = Number(quarter);
    return `(${FISCAL_Q_START[q - 1]} ${q === 4 ? year : year - 1} – ${FISCAL_Q_END[q - 1]} ${year})`;
  }

  if (quarter === "all") return `(Jan ${year} – Dec ${year})`;
  return `(${year} Q${quarter})`;
}

export function buildYearOptions(yearType: YearType) {
  const currentYear =
    yearType === "fiscal" ? currentFiscalYear() : new Date().getFullYear();
  const endYear = Math.max(currentYear, 2027);
  const years = [];
  for (let year = 2024; year <= endYear; year += 1) {
    years.push(year);
  }
  return years;
}
