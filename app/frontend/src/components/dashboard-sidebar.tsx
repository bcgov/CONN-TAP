"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home } from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Home", icon: Home },
];

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <nav className="dashboard-sidebar" aria-label="Main navigation">
      <ul className="dashboard-sidebar__list">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <li key={href}>
              <Link
                href={href}
                className={`dashboard-sidebar__item${isActive ? " dashboard-sidebar__item--active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                <span className="dashboard-sidebar__icon">
                  <Icon size={20} aria-hidden="true" />
                </span>
                <span className="dashboard-sidebar__label">{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
