import { GithubIcon } from "@/components/icons/github";
import { Heart, Mail, X } from "lucide-react";
import Link from "next/link";

const currentYear = new Date().getFullYear();

const footerLinks = {
  product: [
    { name: "Features", href: "/#features" },
    { name: "Attractions", href: "/attractions" },
    { name: "Hotels", href: "/hotels" },
    { name: "Itinerary Planner", href: "/itinerary" },
  ],
  resources: [
    { name: "Documentation", href: "#" },
    { name: "API Reference", href: "#" },
    { name: "Travel Guides", href: "#" },
    { name: "Blog", href: "#" },
  ],
  company: [
    { name: "About Us", href: "#" },
    { name: "Careers", href: "#" },
    { name: "Contact", href: "#" },
    { name: "Press", href: "#" },
  ],
  legal: [
    { name: "Privacy Policy", href: "#" },
    { name: "Terms of Service", href: "#" },
    { name: "Cookie Policy", href: "#" },
  ],
};

const socialLinks = [
  { name: "X (Twitter)", icon: X, href: "#" },
  {
    name: "GitHub",
    icon: GithubIcon,
    href: "https://github.com/FudanSELab/TripSphere",
  },
  { name: "Email", icon: Mail, href: "mailto:contact@tripsphere.com" },
];

export function Footer() {
  return (
    <footer className="bg-card text-card-foreground">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-5 lg:gap-12">
          {/* Brand */}
          <div className="col-span-2 lg:col-span-1">
            <Link href="/" className="flex items-center gap-2">
              <div className="bg-primary text-primary-foreground flex h-10 w-10 items-center justify-center rounded-xl text-xl font-bold">
                T
              </div>
              <span className="text-foreground text-xl font-bold">
                TripSphere
              </span>
            </Link>
            <p className="text-muted-foreground mt-4 max-w-xs text-sm">
              Your intelligent travel companion. Plan, explore, and create
              unforgettable memories with AI-powered assistance.
            </p>
            <div className="mt-6 flex items-center gap-4">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.name}
                    href={social.href}
                    className="bg-muted text-muted-foreground hover:bg-primary hover:text-primary-foreground flex h-10 w-10 items-center justify-center rounded-lg transition-all duration-200"
                    title={social.name}
                  >
                    <Icon className="h-5 w-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="text-foreground mb-4 text-sm font-semibold tracking-wider uppercase">
              Product
            </h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h3 className="text-foreground mb-4 text-sm font-semibold tracking-wider uppercase">
              Resources
            </h3>
            <ul className="space-y-3">
              {footerLinks.resources.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="text-foreground mb-4 text-sm font-semibold tracking-wider uppercase">
              Company
            </h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="text-foreground mb-4 text-sm font-semibold tracking-wider uppercase">
              Legal
            </h3>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.name}>
                  <a
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-border mt-12 border-t pt-8">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <p className="text-muted-foreground text-sm">
              &copy; {currentYear} TripSphere. All rights reserved.
            </p>
            <p className="text-muted-foreground flex items-center gap-1 text-sm">
              Made with{" "}
              <Heart className="fill-destructive text-destructive h-4 w-4" /> by
              the TripSphere Team
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
