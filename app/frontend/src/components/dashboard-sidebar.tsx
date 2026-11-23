"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Settings } from "lucide-react";

const ADMIN_ITEM = { href: "/admin", label: "Admin", icon: Settings };

// homeHref: the user's own dashboard (the BGE dashboard for org users).
// showAdmin: the Admin link, for TO admins only. The /admin page checks the
// role itself too.
export function DashboardSidebar({
  homeHref = "/dashboard",
  showAdmin = false,
}: {
  homeHref?: string;
  showAdmin?: boolean;
}) {
  const pathname = usePathname();
  const homeItem = { href: homeHref, label: "Home", icon: Home };
  const items = showAdmin ? [homeItem, ADMIN_ITEM] : [homeItem];

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
