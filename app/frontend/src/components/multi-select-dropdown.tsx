"use client";

import { useEffect, useRef, useState } from "react";

export type SelectOption = { label: string; value: string };

type MultiSelectDropdownProps = {
  options: SelectOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  allLabel?: string;
  placeholder?: string;
};

export function MultiSelectDropdown({
  options,
  selected,
  onChange,
  allLabel,
  placeholder = "All",
}: MultiSelectDropdownProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const toggle = (value: string) => {
    onChange(selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value]);
  };

  const label =
    selected.length === 0
      ? placeholder
      : selected.map((v) => options.find((o) => o.value === v)?.label ?? v).join(", ");

  return (
    <div className="msd" ref={containerRef}>
      <button
        type="button"
        className={`msd__trigger${open ? " msd__trigger--open" : ""}`}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="msd__label">{label}</span>
        <svg className="msd__chevron" viewBox="0 0 10 6" aria-hidden="true">
          <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
        </svg>
      </button>

      {open && (
        <div className="msd__panel" role="listbox" aria-multiselectable="true">
          {allLabel !== undefined && (
            <>
              <label className="msd__option">
                <input
                  type="checkbox"
                  className="msd__checkbox"
                  checked={selected.length === 0}
                  onChange={() => onChange([])}
                />
                <span>{allLabel}</span>
              </label>
              <div className="msd__divider" />
            </>
          )}
          {options.map(({ label: optLabel, value }) => (
            <label key={value} className="msd__option">
              <input
                type="checkbox"
                className="msd__checkbox"
                checked={selected.includes(value)}
                onChange={() => toggle(value)}
              />
              <span>{optLabel}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
