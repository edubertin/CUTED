import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CUTED | Cortes de vídeo com IA no Windows",
  description:
    "Transforme vídeos longos em cortes verticais com legendas, enquadramento e renderização local no Windows.",
  applicationName: "CUTED",
  keywords: ["CUTED", "editor de vídeo", "cortes com IA", "legendas", "Windows"],
  openGraph: {
    title: "CUTED | Do vídeo longo ao corte pronto",
    description:
      "Um editor local para Windows que encontra, prepara e renderiza cortes verticais com IA.",
    type: "website",
    locale: "pt_BR",
    images: [{ url: "/og.png", width: 1280, height: 640, alt: "CUTED" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "CUTED | Do vídeo longo ao corte pronto",
    description:
      "Editor local para Windows com cortes, legendas e enquadramento assistidos por IA.",
    images: ["/og.png"],
  },
  icons: {
    icon: "/assets/cuted-app-icon.png",
    shortcut: "/assets/cuted-app-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
