import Image from "next/image";
import mark from "../../public/brand/mark.png";

/** Shared supplied logo, with a compact mark for small product surfaces. */
export function Brand({ compact = false }: { compact?: boolean }) {
  return <span className={compact ? "brand brand-compact" : "brand"} role={compact ? "img" : undefined} aria-label={compact ? "Sentinel GRC" : undefined}>
    <span className="brand-mark" aria-hidden="true"><Image src={mark} alt="" sizes="120px" priority /></span>
    {!compact && <span className="brand-wordmark">SENTINEL<small>GRC</small></span>}
  </span>;
}
