const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/** `2025-04` -> `Apr`. Periods are month-grain, sortable as plain strings. */
export const formatMonthLabel = (period: string): string =>
  MONTHS[Number(period.split("-")[1]) - 1] ?? period;

/** `2025-04` -> `Apr 2025`. */
const formatPeriodLabel = (period: string): string =>
  `${formatMonthLabel(period)} ${period.split("-")[0]}`;

export const buildPeriodRangeLabel = (periods: string[]): string => {
  if (periods.length === 0) return "";
  const first = formatPeriodLabel(periods[0]);
  const last = formatPeriodLabel(periods[periods.length - 1]);
  return first === last ? `(${first})` : `(${first} – ${last})`;
};
