export const fmtMillions = (millions: number): string => {
  const rounded = parseFloat(millions.toFixed(2));
  return `$${rounded % 1 === 0 ? rounded.toFixed(0) : String(rounded).replace(/\.?0+$/, "")}M`;
};

export const fmtMillionsFixed = (millions: number): string => `$${millions.toFixed(1)}M`;
