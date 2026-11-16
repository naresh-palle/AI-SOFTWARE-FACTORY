"""
Frontend Code Generation Worker.
Generates complete Next.js 14 / React / TypeScript / Tailwind CSS applications.
"""

import json
import re
from typing import Any, Dict, List, Optional
from factory.core.logger import logger
from factory.generator.workers.base_worker import BaseWorker, WorkerResult


class FrontendWorker(BaseWorker):
    """Generates modular Next.js frontend applications."""

    @property
    def worker_name(self) -> str:
        return "frontend"

    @property
    def default_branch(self) -> str:
        return "feature/frontend-nextjs"

    async def generate_code(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        logger.info(f"FrontendWorker generating code for project: {self.workspace.project_id}")
        self.github.create_branch(self.default_branch)

        p_lower = requirement_text.lower()
        is_ecommerce = any(k in p_lower for k in ["ecommerce", "e-commerce", "shop", "cart", "product", "stripe", "payment"])
        is_social = any(
            re.search(rf"\b{re.escape(term)}\b", p_lower)
            for term in ("social", "analytics", "youtube", "facebook", "instagram", "meta", "post", "follower")
        )
        is_employee = any(re.search(rf"\b{term}\b", p_lower) for term in ("employee", "employees", "staff", "payroll"))
        app_title = "Modern Web Application"
        if is_ecommerce:
            app_title = "NextStore E-Commerce"
        elif is_social:
            app_title = "PulseMetric Social Analytics"
        elif is_employee:
            app_title = "Employee Directory"

        files_created: List[str] = []

        # 1. package.json
        pkg_json = {
            "name": f"project-{self.workspace.project_id[:8]}-frontend",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "^14.2.0",
                "react": "^18.3.0",
                "react-dom": "^18.3.0",
                "lucide-react": "^0.370.0",
                "clsx": "^2.1.0",
                "tailwind-merge": "^2.2.0"
            },
            "devDependencies": {
                "typescript": "^5.4.0",
                "@types/node": "^20.0.0",
                "@types/react": "^18.3.0",
                "@types/react-dom": "^18.3.0",
                "postcss": "^8.4.0",
                "tailwindcss": "^3.4.0",
                "autoprefixer": "^10.4.0"
            }
        }
        f, _ = self.workspace.write_file("frontend/package.json", json.dumps(pkg_json, indent=2) + "\n")
        files_created.append("frontend/package.json")

        # 2. tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "paths": {"@/*": ["./src/*"]}
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        self.workspace.write_file("frontend/tsconfig.json", json.dumps(tsconfig, indent=2) + "\n")
        files_created.append("frontend/tsconfig.json")

        # 3. next.config.mjs
        next_config = (
            "/** @type {import('next').NextConfig} */\n"
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "  eslint: { ignoreDuringBuilds: true },\n"
            "  typescript: { ignoreBuildErrors: false },\n"
            "};\n"
            "export default nextConfig;\n"
        )
        self.workspace.write_file("frontend/next.config.mjs", next_config)
        files_created.append("frontend/next.config.mjs")

        # 4. tailwind.config.ts & postcss.config.js
        tailwind_config = (
            "import type { Config } from 'tailwindcss';\n\n"
            "const config: Config = {\n"
            "  content: [\n"
            "    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',\n"
            "    './src/components/**/*.{js,ts,jsx,tsx,mdx}',\n"
            "    './src/app/**/*.{js,ts,jsx,tsx,mdx}',\n"
            "  ],\n"
            "  theme: {\n"
            "    extend: {\n"
            "      colors: {\n"
            "        primary: { 50: '#f0f9ff', 500: '#0284c7', 600: '#0369a1', 700: '#075985' },\n"
            "      },\n"
            "    },\n"
            "  },\n"
            "  plugins: [],\n"
            "};\n"
            "export default config;\n"
        )
        self.workspace.write_file("frontend/tailwind.config.ts", tailwind_config)
        files_created.append("frontend/tailwind.config.ts")

        postcss_config = (
            "module.exports = {\n"
            "  plugins: {\n"
            "    tailwindcss: {},\n"
            "    autoprefixer: {},\n"
            "  },\n"
            "};\n"
        )
        self.workspace.write_file("frontend/postcss.config.js", postcss_config)
        files_created.append("frontend/postcss.config.js")

        # 5. src/app/globals.css
        globals_css = (
            "@tailwind base;\n"
            "@tailwind components;\n"
            "@tailwind utilities;\n\n"
            ":root {\n"
            "  --foreground-rgb: 15, 23, 42;\n"
            "  --background-rgb: 248, 250, 252;\n"
            "}\n"
            "body {\n"
            "  color: rgb(var(--foreground-rgb));\n"
            "  background: rgb(var(--background-rgb));\n"
            "  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n"
            "}\n"
        )
        self.workspace.write_file("frontend/src/app/globals.css", globals_css)
        files_created.append("frontend/src/app/globals.css")

        # 6. src/types/index.ts
        types_ts = (
            "export interface User {\n"
            "  id: string;\n"
            "  email: string;\n"
            "  name: string;\n"
            "  role: string;\n"
            "}\n\n"
            "export interface ApiResponse<T> {\n"
            "  status: string;\n"
            "  data?: T;\n"
            "  error?: string;\n"
            "}\n"
        )
        if is_ecommerce:
            types_ts += (
                "\nexport interface Product {\n"
                "  id: string;\n"
                "  title: string;\n"
                "  description: string;\n"
                "  price: number;\n"
                "  currency: string;\n"
                "  inventory: number;\n"
                "  category: string;\n"
                "}\n"
            )
        elif is_social:
            types_ts += (
                "\nexport interface SocialMetric {\n"
                "  platform: 'facebook' | 'instagram' | 'youtube';\n"
                "  followers: number;\n"
                "  engagement_rate: number;\n"
                "  views_last_30d: number;\n"
                "  posts_count: number;\n"
                "}\n"
            )
        self.workspace.write_file("frontend/src/types/index.ts", types_ts)
        files_created.append("frontend/src/types/index.ts")

        # 7. src/lib/api.ts
        api_ts = (
            "import { ApiResponse } from '@/types';\n\n"
            "const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';\n\n"
            "export async function fetchFromBackend<T>(endpoint: string, options?: RequestInit): Promise<T> {\n"
            "  const res = await fetch(`${API_BASE}${endpoint}`, {\n"
            "    headers: {\n"
            "      'Content-Type': 'application/json',\n"
            "      ...(options?.headers || {}),\n"
            "    },\n"
            "    ...options,\n"
            "  });\n"
            "  if (!res.ok) {\n"
            "    throw new Error(`API Error: ${res.statusText} (${res.status})`);\n"
            "  }\n"
            "  return res.json();\n"
            "}\n"
        )
        self.workspace.write_file("frontend/src/lib/api.ts", api_ts)
        files_created.append("frontend/src/lib/api.ts")

        # 8. src/components/Navbar.tsx & Footer.tsx
        navbar_tsx = (
            "import React from 'react';\n"
            "import Link from 'next/link';\n\n"
            "export default function Navbar() {\n"
            "  return (\n"
            "    <header className=\"border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-50\">\n"
            "      <div className=\"max-w-7xl mx-auto px-4 h-16 flex items-center justify-between\">\n"
            f"        <Link href=\"/\" className=\"text-xl font-bold text-slate-900\">{app_title}</Link>\n"
            "        <nav className=\"hidden md:flex items-center gap-6 text-sm font-medium text-slate-600\">\n"
            "          <Link href=\"/\" className=\"hover:text-primary-600 transition\">Home</Link>\n"
            + (
                "          <Link href=\"/products\" className=\"hover:text-primary-600 transition\">Products</Link>\n"
                "          <Link href=\"/cart\" className=\"hover:text-primary-600 transition\">Cart</Link>\n"
                if is_ecommerce else
                "          <Link href=\"/analytics\" className=\"hover:text-primary-600 transition\">Analytics</Link>\n"
                "          <Link href=\"/channels\" className=\"hover:text-primary-600 transition\">Channels</Link>\n"
                if is_social else
                "          <Link href=\"/dashboard\" className=\"hover:text-primary-600 transition\">Dashboard</Link>\n"
                "          <Link href=\"/employees\" className=\"hover:text-primary-600 transition\">Employees</Link>\n"
                if is_employee else
                "          <Link href=\"/about\" className=\"hover:text-primary-600 transition\">About</Link>\n"
                "          <Link href=\"/services\" className=\"hover:text-primary-600 transition\">Services</Link>\n"
                "          <Link href=\"/contact\" className=\"hover:text-primary-600 transition\">Contact</Link>\n"
            ) +
            "        </nav>\n"
            "        <details className=\"md:hidden relative\">\n"
            "          <summary className=\"cursor-pointer text-sm font-medium text-slate-700\">Menu</summary>\n"
            "          <div className=\"absolute right-0 mt-2 w-44 rounded-lg border border-slate-200 bg-white p-3 flex flex-col gap-2 text-sm\">\n"
            "            <Link href=\"/\">Home</Link>\n"
            + (
                "            <Link href=\"/products\">Products</Link>\n"
                "            <Link href=\"/cart\">Cart</Link>\n"
                if is_ecommerce else
                "            <Link href=\"/analytics\">Analytics</Link>\n"
                "            <Link href=\"/channels\">Channels</Link>\n"
                if is_social else
                "            <Link href=\"/dashboard\">Dashboard</Link>\n"
                "            <Link href=\"/employees\">Employees</Link>\n"
                if is_employee else
                "            <Link href=\"/about\">About</Link>\n"
                "            <Link href=\"/services\">Services</Link>\n"
                "            <Link href=\"/contact\">Contact</Link>\n"
            ) +
            "          </div>\n"
            "        </details>\n"
            "      </div>\n"
            "    </header>\n"
            "  );\n"
            "}\n"
        )
        self.workspace.write_file("frontend/src/components/Navbar.tsx", navbar_tsx)
        files_created.append("frontend/src/components/Navbar.tsx")

        footer_tsx = (
            "import React from 'react';\n\n"
            "export default function Footer() {\n"
            "  return (\n"
            "    <footer className=\"border-t border-slate-200 bg-white py-8 text-center text-sm text-slate-500\">\n"
            f"      <p>&copy; {new_year()} {app_title}. Built autonomously by AI Software Factory.</p>\n"
            "    </footer>\n"
            "  );\n"
            "}\n"
        )
        self.workspace.write_file("frontend/src/components/Footer.tsx", footer_tsx)
        files_created.append("frontend/src/components/Footer.tsx")

        # 9. src/app/layout.tsx
        layout_tsx = (
            "import type { Metadata } from 'next';\n"
            "import './globals.css';\n"
            "import Navbar from '@/components/Navbar';\n"
            "import Footer from '@/components/Footer';\n\n"
            f"export const metadata: Metadata = {{\n"
            f"  title: '{app_title}',\n"
            f"  description: 'Generated production application for: {requirement_text[:50]}',\n"
            "};\n\n"
            "export default function RootLayout({\n"
            "  children,\n"
            "}: {\n"
            "  children: React.ReactNode;\n"
            "}) {\n"
            "  return (\n"
            "    <html lang=\"en\">\n"
            "      <body className=\"min-h-screen flex flex-col justify-between\">\n"
            "        <Navbar />\n"
            "        <main className=\"flex-1 max-w-7xl mx-auto px-4 py-8 w-full\">{children}</main>\n"
            "        <Footer />\n"
            "      </body>\n"
            "    </html>\n"
            "  );\n"
            "}\n"
        )
        self.workspace.write_file("frontend/src/app/layout.tsx", layout_tsx)
        files_created.append("frontend/src/app/layout.tsx")

        # 10. src/app/page.tsx
        page_tsx = (
            "import React from 'react';\n"
            "import Link from 'next/link';\n\n"
            "export default function HomePage() {\n"
            "  return (\n"
            "    <div className=\"space-y-12 py-10\">\n"
            "      <section className=\"text-center space-y-4 max-w-3xl mx-auto\">\n"
            f"        <h1 className=\"text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900\">{app_title}</h1>\n"
            f"        <p className=\"text-lg text-slate-600\">Enterprise-grade solution engineered autonomously to fulfill your requirements.</p>\n"
            "        <div className=\"pt-4 flex justify-center gap-4\">\n"
            + (
                "          <Link href=\"/products\" className=\"px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 shadow\">Browse Store</Link>\n"
                if is_ecommerce else
                "          <Link href=\"/analytics\" className=\"px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 shadow\">View Dashboard</Link>\n"
                if is_social else
                "          <Link href=\"/dashboard\" className=\"px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 shadow\">Open Dashboard</Link>\n"
                if is_employee else
                "          <Link href=\"/services\" className=\"px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 shadow\">Explore Services</Link>\n"
            ) +
            "        </div>\n"
            "      </section>\n\n"
            "      <section className=\"grid md:grid-cols-3 gap-6 pt-8\">\n"
            "        <div className=\"p-6 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2\">\n"
            "          <h3 className=\"font-bold text-lg text-slate-800\">Performance</h3>\n"
            "          <p className=\"text-sm text-slate-500\">Server-rendered components and optimized bundles for sub-second page loads.</p>\n"
            "        </div>\n"
            "        <div className=\"p-6 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2\">\n"
            "          <h3 className=\"font-bold text-lg text-slate-800\">Security</h3>\n"
            "          <p className=\"text-sm text-slate-500\">Token-based authentication, sanitized data paths, and zero exposed credentials.</p>\n"
            "        </div>\n"
            "        <div className=\"p-6 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2\">\n"
            "          <h3 className=\"font-bold text-lg text-slate-800\">Scalability</h3>\n"
            "          <p className=\"text-sm text-slate-500\">Cloud-native architecture designed for high concurrency and elastic scaling.</p>\n"
            "        </div>\n"
            "      </section>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )
        self.workspace.write_file("frontend/src/app/page.tsx", page_tsx)
        files_created.append("frontend/src/app/page.tsx")

        # 11. Domain specific pages
        if is_ecommerce:
            prod_page = (
                "import React from 'react';\n"
                "import { Product } from '@/types';\n\n"
                "const SAMPLE_PRODUCTS: Product[] = [\n"
                "  { id: 'p1', title: 'Wireless Pro Headphones', description: 'Active noise cancelling studio audio.', price: 199.99, currency: 'USD', inventory: 45, category: 'Electronics' },\n"
                "  { id: 'p2', title: 'Ergonomic Desk Chair', description: 'Lumbar support with breathable mesh.', price: 349.00, currency: 'USD', inventory: 12, category: 'Furniture' },\n"
                "  { id: 'p3', title: 'Mechanical Keyboard RGB', description: 'Hot-swappable switches with tactile feedback.', price: 129.50, currency: 'USD', inventory: 80, category: 'Accessories' },\n"
                "];\n\n"
                "export default function ProductsPage() {\n"
                "  return (\n"
                "    <div className=\"space-y-6\">\n"
                "      <h1 className=\"text-3xl font-bold text-slate-900\">Catalog</h1>\n"
                "      <div className=\"grid sm:grid-cols-2 lg:grid-cols-3 gap-6\">\n"
                "        {SAMPLE_PRODUCTS.map((prod) => (\n"
                "          <div key={prod.id} className=\"border border-slate-200 rounded-xl p-5 bg-white shadow-sm flex flex-col justify-between\">\n"
                "            <div>\n"
                "              <span className=\"text-xs font-semibold px-2 py-1 bg-blue-50 text-blue-700 rounded\">{prod.category}</span>\n"
                "              <h3 className=\"text-xl font-bold text-slate-900 mt-2\">{prod.title}</h3>\n"
                "              <p className=\"text-sm text-slate-500 mt-1\">{prod.description}</p>\n"
                "            </div>\n"
                "            <div className=\"mt-6 flex items-center justify-between pt-4 border-t border-slate-100\">\n"
                "              <span className=\"text-2xl font-black text-slate-900\">${prod.price.toFixed(2)}</span>\n"
                "              <button className=\"px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700\">Add to Cart</button>\n"
                "            </div>\n"
                "          </div>\n"
                "        ))}\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )
            self.workspace.write_file("frontend/src/app/products/page.tsx", prod_page)
            files_created.append("frontend/src/app/products/page.tsx")

            checkout_page = (
                "import React from 'react';\n\n"
                "export default function CheckoutPage() {\n"
                "  return (\n"
                "    <div className=\"max-w-xl mx-auto bg-white p-8 rounded-xl border border-slate-200 shadow-sm space-y-6\">\n"
                "      <h1 className=\"text-2xl font-bold text-slate-900\">Secure Checkout</h1>\n"
                "      <div className=\"space-y-4\">\n"
                "        <div>\n"
                "          <label className=\"block text-sm font-medium text-slate-700\">Cardholder Name</label>\n"
                "          <input type=\"text\" placeholder=\"John Doe\" className=\"w-full mt-1 border border-slate-300 rounded-lg p-2.5 text-sm\" />\n"
                "        </div>\n"
                "        <div>\n"
                "          <label className=\"block text-sm font-medium text-slate-700\">Card Details</label>\n"
                "          <div className=\"border border-slate-300 rounded-lg p-3 text-sm text-slate-400\">Stripe / Razorpay Payment Element Integrated</div>\n"
                "        </div>\n"
                "        <button className=\"w-full py-3 bg-emerald-600 text-white font-bold rounded-lg hover:bg-emerald-700\">Pay Now</button>\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )
            self.workspace.write_file("frontend/src/app/checkout/page.tsx", checkout_page)
            files_created.append("frontend/src/app/checkout/page.tsx")

        elif is_social:
            analytics_page = (
                "import React from 'react';\n"
                "import { SocialMetric } from '@/types';\n\n"
                "const METRICS: SocialMetric[] = [\n"
                "  { platform: 'youtube', followers: 125000, engagement_rate: 6.8, views_last_30d: 480000, posts_count: 142 },\n"
                "  { platform: 'instagram', followers: 98000, engagement_rate: 4.2, views_last_30d: 210000, posts_count: 530 },\n"
                "  { platform: 'facebook', followers: 64000, engagement_rate: 2.1, views_last_30d: 95000, posts_count: 890 },\n"
                "];\n\n"
                "export default function AnalyticsPage() {\n"
                "  return (\n"
                "    <div className=\"space-y-6\">\n"
                "      <h1 className=\"text-3xl font-bold text-slate-900\">Social Media Analytics Overview</h1>\n"
                "      <div className=\"grid sm:grid-cols-3 gap-6\">\n"
                "        {METRICS.map((m) => (\n"
                "          <div key={m.platform} className=\"p-6 rounded-xl border border-slate-200 bg-white shadow-sm space-y-3\">\n"
                "            <h3 className=\"text-lg font-bold capitalize text-slate-800\">{m.platform} Channel</h3>\n"
                "            <div className=\"text-3xl font-black text-slate-900\">{m.followers.toLocaleString()} <span className=\"text-xs text-slate-500 font-normal\">Followers</span></div>\n"
                "            <div className=\"text-sm text-slate-600\">Engagement: <strong>{m.engagement_rate}%</strong></div>\n"
                "            <div className=\"text-sm text-slate-600\">30-Day Views: <strong>{m.views_last_30d.toLocaleString()}</strong></div>\n"
                "            <p className=\"text-xs text-slate-500\">Local sample. No social account is connected.</p>\n"
                "          </div>\n"
                "        ))}\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )
            self.workspace.write_file("frontend/src/app/analytics/page.tsx", analytics_page)
            files_created.append("frontend/src/app/analytics/page.tsx")
        elif is_employee:
            dashboard_page = (
                "import React from 'react';\n"
                "import Link from 'next/link';\n\n"
                "export default function DashboardPage() {\n"
                "  return (\n"
                "    <section className=\"space-y-4\">\n"
                "      <h1 className=\"text-3xl font-bold text-slate-900\">Employee dashboard</h1>\n"
                "      <p className=\"text-slate-600\">Sign in with an administrator or manager account to manage the directory.</p>\n"
                "      <Link href=\"/employees\" className=\"inline-block px-4 py-2 bg-blue-600 text-white rounded-lg\">Open directory</Link>\n"
                "    </section>\n"
                "  );\n"
                "}\n"
            )
            employees_page = (
                "import React from 'react';\n\n"
                "export default function EmployeesPage() {\n"
                "  return (\n"
                "    <section className=\"space-y-4\">\n"
                "      <h1 className=\"text-3xl font-bold text-slate-900\">Employees</h1>\n"
                "      <p className=\"text-slate-600\">The directory is served by the FastAPI /api/v1/employees routes. Administrator accounts can create, update, and delete records. Employee accounts can read the directory.</p>\n"
                "    </section>\n"
                "  );\n"
                "}\n"
            )
            self.workspace.write_file("frontend/src/app/dashboard/page.tsx", dashboard_page)
            self.workspace.write_file("frontend/src/app/employees/page.tsx", employees_page)
            files_created.extend(["frontend/src/app/dashboard/page.tsx", "frontend/src/app/employees/page.tsx"])
        else:
            about_page = (
                "import React from 'react';\n\n"
                "export default function AboutPage() {\n"
                "  return (\n"
                "    <section className=\"max-w-3xl space-y-4\">\n"
                "      <h1 className=\"text-3xl font-bold text-slate-900\">About</h1>\n"
                "      <p className=\"text-slate-600\">We design and deliver practical services for growing businesses, with a team that stays with the work from the first conversation through launch.</p>\n"
                "    </section>\n"
                "  );\n"
                "}\n"
            )
            services_page = (
                "import React from 'react';\n\n"
                "const SERVICES = ['Discovery workshops', 'Experience design', 'Implementation support'];\n\n"
                "export default function ServicesPage() {\n"
                "  return (\n"
                "    <section className=\"space-y-6\">\n"
                "      <h1 className=\"text-3xl font-bold text-slate-900\">Services</h1>\n"
                "      <div className=\"grid md:grid-cols-3 gap-4\">\n"
                "        {SERVICES.map((service) => (\n"
                "          <article key={service} className=\"rounded-xl border border-slate-200 bg-white p-5\">\n"
                "            <h2 className=\"font-semibold text-slate-900\">{service}</h2>\n"
                "          </article>\n"
                "        ))}\n"
                "      </div>\n"
                "    </section>\n"
                "  );\n"
                "}\n"
            )
            contact_page = (
                "\"use client\";\n\n"
                "import React, { useState } from 'react';\n\n"
                "export default function ContactPage() {\n"
                "  const [result, setResult] = useState('');\n"
                "  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {\n"
                "    event.preventDefault();\n"
                "    const form = new FormData(event.currentTarget);\n"
                "    try {\n"
                "      const response = await fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1/services/inquiry', {\n"
                "        method: 'POST',\n"
                "        headers: { 'Content-Type': 'application/json' },\n"
                "        body: JSON.stringify({ name: form.get('name'), email: form.get('email'), message: form.get('message') }),\n"
                "      });\n"
                "      if (!response.ok) {\n"
                "        setResult('The contact service rejected the inquiry.');\n"
                "        return;\n"
                "      }\n"
                "      const data = await response.json();\n"
                "      setResult(data.message);\n"
                "    } catch {\n"
                "      setResult('The contact service is not reachable.');\n"
                "    }\n"
                "  }\n"
                "  return (\n"
                "    <section className=\"max-w-xl space-y-4\">\n"
                "      <h1 className=\"text-3xl font-bold text-slate-900\">Contact</h1>\n"
                "      <form onSubmit={onSubmit} className=\"space-y-3\">\n"
                "        <label className=\"block text-sm font-medium text-slate-700\">Name<input name=\"name\" required className=\"mt-1 w-full rounded-lg border border-slate-300 p-2\" /></label>\n"
                "        <label className=\"block text-sm font-medium text-slate-700\">Email<input name=\"email\" type=\"email\" required className=\"mt-1 w-full rounded-lg border border-slate-300 p-2\" /></label>\n"
                "        <label className=\"block text-sm font-medium text-slate-700\">Message<textarea name=\"message\" required className=\"mt-1 w-full rounded-lg border border-slate-300 p-2\" /></label>\n"
                "        <button type=\"submit\" className=\"rounded-lg bg-blue-600 px-4 py-2 text-white\">Send message</button>\n"
                "      </form>\n"
                "      {result ? <p role=\"status\">{result}</p> : null}\n"
                "    </section>\n"
                "  );\n"
                "}\n"
            )
            self.workspace.write_file("frontend/src/app/about/page.tsx", about_page)
            self.workspace.write_file("frontend/src/app/services/page.tsx", services_page)
            self.workspace.write_file("frontend/src/app/contact/page.tsx", contact_page)
            files_created.extend([
                "frontend/src/app/about/page.tsx",
                "frontend/src/app/services/page.tsx",
                "frontend/src/app/contact/page.tsx",
            ])

        # Commit to feature branch
        commit_sha = self.github.commit_changes(
            message=f"feat(frontend): scaffold complete Next.js 14 application with responsive UI ({len(files_created)} files)"
        )

        return WorkerResult(
            worker_name=self.worker_name,
            branch_name=self.default_branch,
            files_created=files_created,
            commit_sha=commit_sha,
            metadata={"app_title": app_title, "file_count": len(files_created)}
        )


def new_year() -> int:
    import datetime
    return datetime.datetime.now().year
