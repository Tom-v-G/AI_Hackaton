import { useEffect, useRef } from "react";

function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

interface MatrixRainProps {
  color?: string;
  highlight?: string;
}

/**
 * Geanimeerde matrix-rain achtergrond (canvas) — vallende glyphs, zoals het
 * ThreatPulse-design. Vult de parent, draait rustig op requestAnimationFrame
 * en respecteert prefers-reduced-motion (statisch frame i.p.v. animatie).
 */
export function MatrixRain({
  color = "rgba(57,255,136,0.75)",
  highlight = "#eaffef",
}: MatrixRainProps) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const parent = canvas?.parentElement;
    if (!canvas || !parent) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const fs = 14;
    const glyphs = "アカサタナハマヤラワ0123456789ABCDEF<>=/\\$#*+｜:".split("");
    let cols = 0;
    let drops: number[] = [];

    const fit = () => {
      canvas.width = parent.offsetWidth;
      canvas.height = parent.offsetHeight;
      cols = Math.floor(canvas.width / fs) || 1;
      drops = Array(cols)
        .fill(0)
        .map(() => Math.random() * -60);
    };
    fit();

    if (prefersReducedMotion()) {
      ctx.font = `${fs}px monospace`;
      ctx.fillStyle = color;
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < canvas.height / fs; j += 3) {
          if (Math.random() < 0.15) {
            ctx.fillText(glyphs[(Math.random() * glyphs.length) | 0], i * fs, j * fs);
          }
        }
      }
      return;
    }

    let raf = 0;
    let last = 0;
    const step = (t: number) => {
      raf = requestAnimationFrame(step);
      if (t - last < 58) return;
      last = t;
      ctx.fillStyle = "rgba(2,6,4,0.16)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = `${fs}px monospace`;
      for (let i = 0; i < cols; i++) {
        const ch = glyphs[(Math.random() * glyphs.length) | 0];
        const x = i * fs;
        const y = drops[i] * fs;
        ctx.fillStyle = Math.random() < 0.035 ? highlight : color;
        ctx.fillText(ch, x, y);
        if (y > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    };
    raf = requestAnimationFrame(step);

    const ro = new ResizeObserver(fit);
    ro.observe(parent);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [color, highlight]);

  return (
    <canvas
      ref={ref}
      className="pointer-events-none absolute inset-0 h-full w-full"
      aria-hidden="true"
    />
  );
}
