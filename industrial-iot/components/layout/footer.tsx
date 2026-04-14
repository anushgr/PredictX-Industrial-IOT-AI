import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-8 border-t border-slate-800/80 px-4 py-4 text-xs text-slate-500 sm:px-6">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <span>© 2026 PredictX Industrial AI</span>
        <span>Version 2.1.0</span>
        <span>API Status: Healthy</span>
        <Link href="#" className="hover:text-cyan-300">
          Support
        </Link>
        <Link href="#" className="hover:text-cyan-300">
          Docs
        </Link>
      </div>
    </footer>
  );
}
