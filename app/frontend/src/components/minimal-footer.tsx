"use client";

const LINKS = [
  { label: "Home", href: "https://www2.gov.bc.ca/gov/content/home" },
  { label: "Disclaimer", href: "https://www2.gov.bc.ca/gov/content?id=79F93E018712422FBC8E674A67A70535" },
  { label: "Privacy", href: "https://www2.gov.bc.ca/gov/content?id=9E890E16955E4FF4BF3B0E07B4722932" },
  { label: "Accessibility", href: "https://www2.gov.bc.ca/gov/content?id=E08E79740F9C41B9B0C484685CC5E412" },
  { label: "Copyright", href: "https://www2.gov.bc.ca/gov/content?id=1AAACC9C65754E4D89A118B875E0FBDA" },
  { label: "Contact Us", href: "https://www2.gov.bc.ca/gov/content?id=6A77C17D0CCB48F897F8598CCC019111" },
];

export function MinimalFooter() {
  return (
    <footer className="minimal-footer">
      <nav aria-label="Footer links" className="minimal-footer__nav">
        <ul className="minimal-footer__links">
          {LINKS.map(({ label, href }) => (
            <li key={label}>
              <a href={href}>{label}</a>
            </li>
          ))}
        </ul>
      </nav>
    </footer>
  );
}
