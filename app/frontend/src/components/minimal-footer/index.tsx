import styles from "./minimal-footer.module.css";

export type FooterLink = {
  label: string;
  href: string;
};

const BC_GOV_LINKS: FooterLink[] = [
  { label: "Home", href: "https://www2.gov.bc.ca/gov/content/home" },
  { label: "Disclaimer", href: "https://www2.gov.bc.ca/gov/content?id=79F93E018712422FBC8E674A67A70535" },
  { label: "Privacy", href: "https://www2.gov.bc.ca/gov/content?id=9E890E16955E4FF4BF3B0E07B4722932" },
  { label: "Accessibility", href: "https://www2.gov.bc.ca/gov/content?id=E08E79740F9C41B9B0C484685CC5E412" },
  { label: "Copyright", href: "https://www2.gov.bc.ca/gov/content?id=1AAACC9C65754E4D89A118B875E0FBDA" },
  { label: "Contact Us", href: "https://www2.gov.bc.ca/gov/content?id=6A77C17D0CCB48F897F8598CCC019111" },
];

type Props = {
  links?: FooterLink[];
};

/** A single row of footer links separated by "|". Defaults to the standard B.C. Government links. */
export function MinimalFooter({ links = BC_GOV_LINKS }: Props) {
  return (
    <footer className={styles.footer}>
      <nav aria-label="Footer links">
        <ul className={styles.links}>
          {links.map(({ label, href }, index) => (
            <li key={label} className={styles.item}>
              {index > 0 && (
                <span className={styles.separator} aria-hidden="true">
                  |
                </span>
              )}
              <a className={styles.link} href={href}>
                {label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </footer>
  );
}
