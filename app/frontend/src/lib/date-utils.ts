export type YearType = "fiscal" | "calendar";

export function currentFiscalYear(date = new Date()) {
  return date.getMonth() >= 3 ? date.getFullYear() + 1 : date.getFullYear();
}

const FISCAL_Q_START = ["Apr", "Jul", "Oct", "Jan"];
const FISCAL_Q_END = ["Jun", "Sep", "Dec", "Mar"];

export function buildDateRangeLabel(yearType: YearType, years: string[], quarters: string[]): string {
  if (years.length === 0) return "";
  const nums = years.map(Number).sort((a, b) => a - b);
  const first = nums[0];
  const last = nums[nums.length - 1];

  if (yearType === "fiscal") {
    if (quarters.length === 0) {
      if (first === last) return `(Apr ${first - 1} – Mar ${first})`;
      return `(Apr ${first - 1} – Mar ${last})`;
    }
    const qs = quarters.map(Number).sort((a, b) => a - b);
    const startLabel = `${FISCAL_Q_START[qs[0] - 1]} ${qs[0] === 4 ? first : first - 1}`;
    const endLabel = `${FISCAL_Q_END[qs[qs.length - 1] - 1]} ${last}`;
    return `(${startLabel} – ${endLabel})`;
  }

  if (quarters.length === 0) {
    if (first === last) return `(Jan ${first} – Dec ${first})`;
    return `(Jan ${first} – Dec ${last})`;
  }
  const qs = quarters.map(Number).sort((a, b) => a - b);
  const qLabels = qs.map((q) => `Q${q}`).join(", ");
  if (first === last) return `(${first} ${qLabels})`;
  return `(${first}–${last} ${qLabels})`;
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
