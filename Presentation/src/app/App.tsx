import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Slide, SLIDES } from "./components/slides";

// Fixed design canvas — every slide is authored to exactly these dimensions and
// the whole canvas is scaled uniformly to fit the viewport. This guarantees a
// slide that fits once fits on every screen (no bottom clipping).
const CANVAS_W = 1600;
const CANVAS_H = 900;
const NAV_RESERVE = 72; // space kept for the bottom navigation bar

export default function App() {
  const [i, setI] = useState(1);
  const [scale, setScale] = useState(1);
  const total = SLIDES.length;

  useEffect(() => {
    const fit = () =>
      setScale(
        Math.min(
          window.innerWidth / CANVAS_W,
          (window.innerHeight - NAV_RESERVE) / CANVAS_H,
        ),
      );
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown")
        setI((v) => Math.min(total, v + 1));
      if (e.key === "ArrowLeft" || e.key === "PageUp")
        setI((v) => Math.max(1, v - 1));
      if (e.key === "Home") setI(1);
      if (e.key === "End") setI(total);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [total]);

  return (
    <div
      className="fixed inset-0 overflow-hidden flex items-center justify-center"
      style={{
        background: "#05080C",
        fontFamily:
          '"IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}
    >
      <div
        className="relative shadow-2xl overflow-hidden"
        style={{
          width: CANVAS_W,
          height: CANVAS_H,
          flex: "none",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      >
        <Slide index={i} />
      </div>

      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-3">
        <button
          onClick={() => setI((v) => Math.max(1, v - 1))}
          disabled={i === 1}
          className="p-2 transition disabled:opacity-30 hover:opacity-80"
          style={{ background: "#0F141B", color: "#fff", border: "1px solid #1F2733" }}
          aria-label="Previous"
        >
          <ChevronLeft size={18} />
        </button>
        <div
          className="tabular-nums px-4 py-2"
          style={{
            background: "#0F141B",
            color: "#fff",
            border: "1px solid #1F2733",
            fontSize: 12,
            letterSpacing: 2,
          }}
        >
          {String(i).padStart(2, "0")} / {String(total).padStart(2, "0")} · ← → to navigate
        </div>
        <button
          onClick={() => setI((v) => Math.min(total, v + 1))}
          disabled={i === total}
          className="p-2 transition disabled:opacity-30 hover:opacity-80"
          style={{ background: "#E5093F", color: "#fff", border: "1px solid #E5093F" }}
          aria-label="Next"
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}
