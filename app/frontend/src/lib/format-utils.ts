export const fmtMillions = (millions: number): string => {
  // Below $1M the millions format costs more than it saves: "$0.08M" reads as
  // near-nothing when it's $80,000, and under $5,000 it collapses to "$0M" and
  // reads as no spend at all. Show whole dollars instead, dropping the M so the
  // unit can't be misread.
  if (Math.abs(millions) < 1) {
    return `$${Math.round(millions * 1_000_000).toLocaleString("en-CA")}`;
  }
  const rounded = parseFloat(millions.toFixed(2));
  return `$${rounded % 1 === 0 ? rounded.toFixed(0) : String(rounded).replace(/\.?0+$/, "")}M`;
};

export const fmtMillionsFixed = (millions: number): string => `$${millions.toFixed(1)}M`;
