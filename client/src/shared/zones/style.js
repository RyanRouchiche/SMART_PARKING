export const LINE_COUNT = 6;

export function lineColor(area) {
  return `var(--line-${((Number(area) - 1) % LINE_COUNT + LINE_COUNT) % LINE_COUNT + 1})`;
}

export function spotCode(area, name) {
  const digits = String(name).match(/\d+/)?.[0];
  return digits ? `Z${area}-P${digits.padStart(2, "0")}` : `Z${area}-${name}`;
}
