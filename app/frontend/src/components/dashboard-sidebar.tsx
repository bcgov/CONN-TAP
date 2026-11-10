"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Settings } from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Home", icon: Home },
];

const ADMIN_ITEM = { href: "/admin", label: "Admin", icon: Settings };

// showAdmin: the Admin link, for TO admins only. The /admin page checks the
// role itself too.
export function DashboardSidebar({ showAdmin = false }: { showAdmin?: boolean }) {
  const pathname = usePathname();
  const items = showAdmin ? [...NAV_ITEMS, ADMIN_ITEM] : NAV_ITEMS;

  return (
    <nav className="dashboard-sidebar" aria-label="Main navigation">
      <ul className="dashboard-sidebar__list">
        {items.map(({ href, label, icon: Icon }) => {
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
