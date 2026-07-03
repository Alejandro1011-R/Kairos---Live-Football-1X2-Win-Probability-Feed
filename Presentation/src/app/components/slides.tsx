import { useState } from "react";
import { motion } from "motion/react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  TrendingUp,
  Target,
  Database,
  DollarSign,
  Activity,
  Zap,
  AlertCircle,
  Layers,
} from "lucide-react";

const ACCENT = "#E5093F";
const ACCENT2 = "#00C2FF";
const INK = "#0A0E14";
const SUB = "#8A95A5";

// Type system: a condensed athletic display face for headlines (scoreboard energy),
// a clean grotesk for reading copy, and a terminal-grade mono for every number —
// the deck reads like a live data feed, not a slide template.
const FONT_DISPLAY = "'Big Shoulders Display', 'Arial Narrow', sans-serif";
const FONT_BODY = "'IBM Plex Sans', sans-serif";
const FONT_MONO = "'IBM Plex Mono', 'SF Mono', monospace";

// 8-slide deck, timed for a 7-minute pitch (~50-90s/slide). Consolidated from an
// earlier 13-slide/15-minute version — every Part 1-4 element (business goal, math
// problem statement, usage scenario, domain research, dataset, economic effect)
// is still present, just merged onto fewer slides so the talk track fits the clock.

// ---------- shared chrome ----------
function SlideShell({
  index,
  total,
  eyebrow,
  children,
}: {
  index: number;
  total: number;
  eyebrow: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="relative w-full h-full overflow-hidden"
      style={{ background: INK, color: "#fff" }}
    >
      {/* top bar */}
      <div
        className="absolute top-0 left-0 right-0 flex items-center justify-between px-10 py-5 z-10"
        style={{ fontFamily: FONT_MONO }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-2 h-6"
            style={{ background: ACCENT }}
          />
          <div
            className="tracking-[0.3em] uppercase"
            style={{ fontSize: 11, color: SUB }}
          >
            Kairos / Live 1X2 Feed
          </div>
        </div>
        <div
          className="tracking-[0.3em] uppercase"
          style={{ fontSize: 11, color: SUB }}
        >
          {eyebrow}
        </div>
        <div
          className="tabular-nums"
          style={{ fontSize: 11, color: SUB, letterSpacing: 2 }}
        >
          {String(index).padStart(2, "0")} / {String(total).padStart(2, "0")}
        </div>
      </div>

      {/* diagonal accent */}
      <div
        className="absolute -right-32 -top-32 w-96 h-96 rotate-45"
        style={{ background: ACCENT, opacity: 0.06 }}
      />

      {/* bottom marker */}
      <div
        className="absolute bottom-0 left-0 right-0 flex items-center justify-end px-10 py-5 z-10"
        style={{ background: `linear-gradient(to top, ${INK} 60%, transparent)` }}
      >
        <div className="flex gap-1">
          {Array.from({ length: total }).map((_, i) => (
            <div
              key={i}
              className="h-[2px]"
              style={{
                width: i === index - 1 ? 28 : 12,
                background: i < index ? ACCENT : "#1F2733",
                transition: "all 250ms",
              }}
            />
          ))}
        </div>
      </div>

      <div
        className="absolute inset-0 px-16 pt-24 pb-24 flex flex-col overflow-hidden"
        style={{ fontFamily: FONT_BODY }}
      >
        {children}
      </div>
    </div>
  );
}

function H1({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: FONT_DISPLAY,
        fontSize: 60,
        lineHeight: 0.98,
        letterSpacing: -0.5,
        fontWeight: 800,
      }}
    >
      {children}
    </div>
  );
}
function H2({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: FONT_DISPLAY,
        fontSize: 44,
        lineHeight: 1.0,
        letterSpacing: -0.3,
        fontWeight: 800,
      }}
    >
      {children}
    </div>
  );
}
function Lead({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: 16.5,
        lineHeight: 1.48,
        color: "#C9D1DA",
        maxWidth: 900,
      }}
    >
      {children}
    </div>
  );
}
function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="uppercase tracking-[0.3em] flex items-center gap-3"
      style={{ fontSize: 11, color: ACCENT, fontWeight: 600, fontFamily: FONT_MONO }}
    >
      <span style={{ width: 14, height: 1, background: ACCENT, display: "inline-block" }} />
      {children}
    </div>
  );
}

// ---------- Slide 1 — Title ----------
function S1Title() {
  return (
    <div className="flex flex-col h-full justify-between">
      <Eyebrow>A B2B Sports-Data Product · 2026</Eyebrow>

      <div>
        <div
          style={{
            fontFamily: FONT_DISPLAY,
            fontSize: 200,
            lineHeight: 0.82,
            letterSpacing: -2,
            fontWeight: 900,
          }}
        >
          KAIROS
        </div>
        <div className="flex items-baseline gap-6 mt-5">
          <div
            className="h-[3px] w-24"
            style={{ background: ACCENT }}
          />
          <div
            style={{
              fontSize: 28,
              letterSpacing: -0.3,
              color: "#E6E9EE",
              fontWeight: 400,
            }}
          >
            Live football 1X2 win-probability feed
          </div>
        </div>
        <div
          className="mt-6"
          style={{ fontSize: 16, color: SUB, maxWidth: 720, lineHeight: 1.6 }}
        >
          Greek — <em>the opportune moment.</em> A calibrated, low-latency probability
          stream for prediction-market operators and sportsbooks pricing in-play markets.
        </div>
      </div>

      <div className="flex gap-12">
        {[
          ["Coverage", "636 intl matches"],
          ["Resolution", "Per-minute, live"],
          ["Edge vs baseline", "+8.4% log-loss"],
          ["Year-1 effect", "≈ $2.7M"],
        ].map(([k, v]) => (
          <div key={k}>
            <div
              className="uppercase tracking-[0.2em]"
              style={{ fontSize: 10, color: SUB, fontFamily: FONT_MONO }}
            >
              {k}
            </div>
            <div
              className="tabular-nums"
              style={{
                fontFamily: FONT_MONO,
                fontSize: 22,
                fontWeight: 600,
                marginTop: 6,
                color: "#F2F4F7",
              }}
            >
              {v}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------- Slide 2 — Market + Business goal (merged) ----------
function S2GoalMarket() {
  const market = [
    { tag: "WC2026", d: "Stats Perform = FIFA's exclusive worldwide betting-data distributor for World Cup 2026 — the biggest betting-data rights window in 4 years." },
    { tag: "Opta PM", d: "Stats Perform launched “Opta for Prediction Markets” — a productised probability feed is now a real, sellable B2B category." },
    { tag: "Market", d: "Kalshi & Polymarket are scaling sports-event contracts faster than the market is pricing them well." },
  ];
  const goal = [
    { k: "Net hold uplift", v: "+0.30", u: "pp", note: "on live in-play handle" },
    { k: "Feed licensing", v: "$30k", u: "/ mo", note: "per operator client" },
    { k: "Trader risk", v: "↓", u: "", note: "tighter spreads, lower exposure" },
  ];
  return (
    <div className="flex flex-col gap-6 h-full">
      <Eyebrow>Market · Why now → Business goal</Eyebrow>
      <H1>
        A buyer that exists today —
        <br /> <span style={{ color: ACCENT }}>losing money live.</span>
      </H1>
      <Lead>
        Mispriced live markets are exactly where operators lose money to sharp
        bettors. Kairos streams calibrated win/draw/away probabilities so the
        operator prices in-play markets tighter, holds a safer margin, and
        reduces trader risk — into a buyer window that's open right now.
      </Lead>
      <div className="grid grid-cols-3 gap-5">
        {market.map((it) => (
          <div
            key={it.tag}
            className="p-5 border"
            style={{ borderColor: "#1F2733", background: "#0F141B" }}
          >
            <div
              className="inline-block px-2 py-1 mb-3"
              style={{ background: ACCENT, fontSize: 10, fontWeight: 700, letterSpacing: 2, fontFamily: FONT_MONO }}
            >
              {it.tag}
            </div>
            <div style={{ fontSize: 13, color: "#C9D1DA", lineHeight: 1.45 }}>{it.d}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-5 mt-auto">
        {goal.map((m) => (
          <div
            key={m.k}
            className="p-5 border flex items-end justify-between"
            style={{ borderColor: "#1F2733", background: "#0F141B" }}
          >
            <div>
              <div
                className="uppercase tracking-[0.2em]"
                style={{ fontSize: 10, color: SUB }}
              >
                {m.k}
              </div>
              <div style={{ fontSize: 12, color: SUB, marginTop: 5 }}>
                {m.note}
              </div>
            </div>
            <div className="tabular-nums flex items-baseline gap-2" style={{ fontFamily: FONT_MONO }}>
              <span style={{ fontSize: 32, fontWeight: 700, color: ACCENT }}>{m.v}</span>
              {m.u && <span style={{ fontSize: 14, fontWeight: 600, color: SUB }}>{m.u}</span>}
            </div>
          </div>
        ))}
      </div>
      <div
        className="uppercase tracking-[0.15em]"
        style={{ fontSize: 10, color: "#4C5867", fontFamily: FONT_MONO }}
      >
        Sources — StatsPerform.com · FIFA media release (WC2026 betting-data rights) · Kalshi · Polymarket
      </div>
    </div>
  );
}

// ---------- Slide 3 — Math problem statement + Dualism (merged) ----------
function S3MathDualism() {
  const rows = [
    { name: "M1 · Scoreboard baseline", sub: "logistic on minute + goal_diff", ll: "0.821", ac: "0.655", ece: "0.051", tone: "neutral" },
    { name: "M2 · Gradient boosting", sub: "uncalibrated — the trap", ll: "1.927", ac: "0.559", ece: "0.211", tone: "bad" },
    { name: "M3 · Kairos", sub: "calibrated logistic + interactions", ll: "0.804", ac: "0.639", ece: "0.023", tone: "good" },
  ];
  return (
    <div className="flex flex-col h-full gap-5">
      <Eyebrow>Math problem statement · Validation</Eyebrow>
      <H1>
        Worse accuracy. <span style={{ color: ACCENT }}>Better</span> money.
      </H1>
      <div className="grid grid-cols-5 gap-8">
        <div
          className="col-span-2 p-5"
          style={{ background: "#000", border: `1px solid ${ACCENT}`, fontFamily: FONT_MONO, fontSize: 14, lineHeight: 1.7 }}
        >
          <div style={{ color: SUB, fontSize: 11 }}># given match state xₜ at live time t</div>
          <div style={{ marginTop: 3 }}>
            <span style={{ color: ACCENT2 }}>P</span>(H), <span style={{ color: ACCENT2 }}>P</span>(D),{" "}
            <span style={{ color: ACCENT2 }}>P</span>(A) — refreshed every minute/event
          </div>
          <div style={{ color: SUB, marginTop: 12, fontSize: 11 }}># scored with proper scoring rules</div>
          <div>log-loss, Brier, <span style={{ color: ACCENT }}>ECE</span> — not accuracy</div>
          <div style={{ color: SUB, marginTop: 12, fontSize: 11 }}># usage scenario</div>
          <div style={{ fontSize: 12.5 }}>
            live events → feature builder → Kairos → P(H,D,A) → operator pricing API
          </div>
        </div>
        <div className="col-span-3">
          <div
            className="grid items-center px-4 py-2 uppercase tracking-[0.15em]"
            style={{
              gridTemplateColumns: "2fr 1fr 1fr 1fr",
              fontSize: 9.5,
              color: SUB,
              fontFamily: FONT_MONO,
              borderBottom: `1px solid #1F2733`,
            }}
          >
            <div>Model</div>
            <div className="text-right">Log-loss ↓</div>
            <div className="text-right">Accuracy</div>
            <div className="text-right">ECE ↓</div>
          </div>
          {rows.map((r) => (
            <div
              key={r.name}
              className="grid items-center px-4 py-3.5 tabular-nums"
              style={{
                gridTemplateColumns: "2fr 1fr 1fr 1fr",
                borderBottom: `1px solid #1F2733`,
                background: r.tone === "good" ? "rgba(229,9,63,0.08)" : "transparent",
              }}
            >
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, fontFamily: FONT_BODY }}>{r.name}</div>
                <div style={{ fontSize: 11, color: SUB, marginTop: 1, fontFamily: FONT_BODY }}>{r.sub}</div>
              </div>
              <div
                className="text-right"
                style={{ fontFamily: FONT_MONO, fontSize: 18, color: r.tone === "bad" ? ACCENT : r.tone === "good" ? ACCENT : "#fff", fontWeight: 700 }}
              >
                {r.ll}
              </div>
              <div className="text-right" style={{ fontFamily: FONT_MONO, fontSize: 18 }}>{r.ac}</div>
              <div
                className="text-right"
                style={{ fontFamily: FONT_MONO, fontSize: 18, color: r.tone === "bad" ? ACCENT : "#fff", fontWeight: 600 }}
              >
                {r.ece}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div
        className="mt-auto p-5"
        style={{ borderLeft: `3px solid ${ACCENT}`, background: "#0F141B" }}
      >
        <div style={{ fontSize: 14.5, color: "#E6E9EE", lineHeight: 1.5 }}>
          M3 actually has <strong>worse accuracy</strong> than M1 (0.639 vs 0.655 —
          optimizing for accuracy picks the wrong model) — yet M3 is meaningfully
          better priced (<strong>−2.1% log-loss</strong>, less than half M1's
          calibration error). M2 looks "only a bit worse" on accuracy but its
          probabilities are{" "}
          <strong>2.4× worse log-loss</strong> and 9× worse calibrated — it would{" "}
          <strong>bleed money in a market</strong>. Accuracy doesn't just miss the
          difference here — it points the wrong way; this same dualism re-appears
          on the real World Cup 2026 track (Results, next).
        </div>
      </div>
    </div>
  );
}

// ---------- Slide 4 — Domain research + Model (merged) ----------
function S4ResearchModel() {
  return (
    <div className="grid grid-cols-2 gap-12 h-full">
      <div className="flex flex-col gap-5">
        <Eyebrow>Domain research</Eyebrow>
        <H1>
          Goal-arrival <span style={{ color: ACCENT }}>process,</span>
          <br /> not snapshot classifier.
        </H1>
        <Lead>
          Robberechts, Van Haaren & Davis (KDD 2021) and Clegg, Song & Cartlidge
          (2026) both model each team's scoring as a Poisson/hazard process whose
          rate is set by a pre-match strength prior. Their headline finding —{" "}
          <strong style={{ color: "#E6E9EE" }}>the prior matters more than the
          model on top of it</strong> — matches how Opta's own supercomputer works:
          betting-market odds + Elo power rankings, because the market price
          digests lineups and form no sparse-schedule rating can see.
        </Lead>
        <div
          className="mt-2 p-4"
          style={{ borderLeft: `3px solid ${ACCENT}`, background: "#0F141B" }}
        >
          <div style={{ fontSize: 13.5, color: "#E6E9EE", lineHeight: 1.5 }}>
            We reproduced that finding independently: on 760 club matches with
            real Pinnacle closing odds, the <strong style={{ color: ACCENT }}>
            market prior alone is worth +4.1% log-loss</strong> — more than every
            in-play covariate combined; real per-minute xG adds ~0% once it's in.
          </div>
        </div>
        <div
          className="uppercase tracking-[0.15em] mt-auto"
          style={{ fontSize: 10, color: "#4C5867", fontFamily: FONT_MONO }}
        >
          arXiv:1906.05029 (Robberechts et al., KDD 2021) · arXiv:2605.16066 (Clegg et al., 2026)
        </div>
      </div>
      <div className="flex flex-col gap-4">
        <Eyebrow>Model</Eyebrow>
        <div
          className="p-5"
          style={{ background: "#000", border: `1px solid ${ACCENT}`, fontFamily: FONT_MONO, fontSize: 13, lineHeight: 1.75 }}
        >
          <div style={{ color: SUB }}># prior — market if it exists, Elo otherwise</div>
          <div>prior = logits(de-vig(odds)) ?? logits(elo_to_hda(elo_diff))</div>
          <div style={{ color: SUB, marginTop: 8 }}># remaining goals per side, live state</div>
          <div>λ_side = rate(prior, goal_diff, red_diff, xg_roll) × time_remaining</div>
          <div style={{ color: SUB, marginTop: 8 }}># Skellam = difference of two Poissons</div>
          <div>
            <span style={{ color: ACCENT2 }}>P</span>(H,D,A) = Skellam(λ_home, λ_away) shifted by goal_diff
          </div>
        </div>
        <div className="flex flex-col gap-2.5">
          {[
            ["01", "Market-anchored prior", "de-vigged odds in training & serving, Elo fallback — worth +4.1% log-loss, measured not assumed"],
            ["02", "Poisson goal-arrival rate", "goal_diff, red_diff, rolling real-xG (has_xg flag, never a proxy) modulate live scoring rate"],
            ["03", "Skellam, closed form", "exact distribution of the goal-count difference — no Monte-Carlo simulation"],
            ["04", "Out-of-fold calibration", "corrects the Skellam independence bias that under-prices the draw (Dixon-Coles) — the largest single gain"],
          ].map(([n, t, d]) => (
            <div
              key={n}
              className="p-3.5 flex gap-4 items-start"
              style={{ background: "#0F141B", border: "1px solid #1F2733" }}
            >
              <div
                className="tabular-nums"
                style={{ fontFamily: FONT_DISPLAY, fontSize: 24, fontWeight: 800, color: ACCENT, width: 34 }}
              >
                {n}
              </div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700 }}>{t}</div>
                <div style={{ fontSize: 12, color: SUB, marginTop: 3, lineHeight: 1.45 }}>{d}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------- Slide 5 — Dataset ----------
function S5Dataset() {
  const tracks = [
    {
      tag: "Proof of concept",
      source: "StatsBomb + football-data.co.uk",
      matches: "760",
      snaps: "69,160",
      detail: "Premier League + La Liga 15/16 · real per-minute shots & xG · Pinnacle closing odds matched 760/760, de-vigged",
    },
    {
      tag: "The real product",
      source: "KickoffAPI + StatsBomb events + eloratings.net + betexplorer.com",
      matches: "636",
      snaps: "57,876",
      detail: "10 major tournaments incl. WC2018/22, Euros, Copa América, AFCON — deduplicated, regulation-time labels, market prior on 616/636 matches (97%), Elo fallback for the rest",
    },
  ];
  return (
    <div className="flex flex-col gap-6 h-full">
      <Eyebrow>Dataset</Eyebrow>
      <H1>
        Two tracks. <span style={{ color: ACCENT }}>Zero</span> fabricated numbers.
      </H1>
      <div className="grid grid-cols-2 gap-6">
        {tracks.map((t) => (
          <div
            key={t.tag}
            className="p-6 flex flex-col gap-3"
            style={{ background: "#0F141B", border: "1px solid #1F2733" }}
          >
            <div
              className="inline-block px-2 py-1 w-fit"
              style={{ background: ACCENT, fontSize: 10, fontWeight: 700, letterSpacing: 2, fontFamily: FONT_MONO }}
            >
              {t.tag}
            </div>
            <div style={{ fontSize: 15, fontWeight: 700 }}>{t.source}</div>
            <div className="flex gap-8 tabular-nums" style={{ fontFamily: FONT_MONO }}>
              <div>
                <div className="uppercase tracking-[0.2em]" style={{ fontSize: 9, color: SUB }}>Matches</div>
                <div style={{ fontSize: 28, fontWeight: 700 }}>{t.matches}</div>
              </div>
              <div>
                <div className="uppercase tracking-[0.2em]" style={{ fontSize: 9, color: SUB }}>Snapshots</div>
                <div style={{ fontSize: 28, fontWeight: 700 }}>{t.snaps}</div>
              </div>
            </div>
            <div style={{ fontSize: 12.5, color: SUB, lineHeight: 1.5 }}>{t.detail}</div>
          </div>
        ))}
      </div>
      <div
        className="mt-auto p-5"
        style={{ borderLeft: `3px solid ${ACCENT}`, background: "#0F141B" }}
      >
        <div style={{ fontSize: 13, color: "#E6E9EE", lineHeight: 1.5 }}>
          Data honesty, enforced three times. A labelled proxy is still fabricated
          data — no ramped per-minute values, ever, only real event streams.
          Official scores include extra time, which silently flips 9 knockouts'
          regulation-time label (incl. the Copa América final) — every label
          recomputed from <strong style={{ color: ACCENT }}>period-1/2 events</strong>.
          And the market prior: <strong style={{ color: ACCENT }}>616/636 matches
          (97%)</strong> now carry a real closing-odds price — 128 via
          football-data.co.uk, 488 scraped from betexplorer.com's public results
          pages against that site's stated terms of service — disclosed here on
          purpose, not the default recommendation for anyone reusing this pipeline
          (the ToS-compliant path is a paid The Odds API plan, already wired via
          market_live.py).
        </div>
      </div>
      <div
        className="uppercase tracking-[0.15em]"
        style={{ fontSize: 10, color: "#4C5867", fontFamily: FONT_MONO }}
      >
        Sources — StatsBomb Open Data · football-data.co.uk · KickoffAPI ·
        eloratings.net · betexplorer.com (scraped) · The Odds API (live)
      </div>
    </div>
  );
}

function Legend2({ dot, label, dashed }: { dot: string; label: string; dashed?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div
        style={{
          width: 22,
          height: 3,
          background: dashed ? "transparent" : dot,
          borderTop: dashed ? `2px dashed ${dot}` : undefined,
        }}
      />
      <div style={{ fontSize: 13, color: "#E6E9EE" }}>{label}</div>
    </div>
  );
}

type MatchTrajectory = {
  fid: number;
  home: string;
  away: string;
  eloHome: number;
  eloAway: number;
  finalScore: string;
  goalEvents: { m: number; score: string }[];
  redEvents: { m: number; side: "home" | "away" }[];
  traj: { m: number; H: number; D: number; A: number }[];
};

// Short codes for the match-picker chips (standard 3-letter country codes,
// not just the first 3 letters — avoids e.g. "Austria" reading as "AUS").
const TEAM_CODE: Record<string, string> = {
  France: "FRA", Sweden: "SWE", Algeria: "ALG", Austria: "AUT",
  Belgium: "BEL", Iran: "IRN", Senegal: "SEN", Iraq: "IRQ",
  Norway: "NOR", Germany: "GER", Paraguay: "PAR",
};

// Six REAL World Cup 2026 matches, live P(H/D/A) trajectories produced by
// live_runner.py's trained GoalProcessModel (Poisson goal-arrival process,
// market/Elo swap-ready prior, out-of-fold recalibration).
// Not simulated, not hand-tuned — same pipeline that produces every other number
// in this deck. Picked for range: blowout, wild comeback draw, goalless stalemate
// with a red card, early-red-card rout, back-and-forth thriller, knockout draw.
const MATCHES: MatchTrajectory[] = [
  {
    fid: 1565177,
    home: "France",
    away: "Sweden",
    eloHome: 2123,
    eloAway: 1742,
    finalScore: "3-0",
    goalEvents: [{ m: 45, score: "1-0" }, { m: 53, score: "2-0" }, { m: 74, score: "3-0" }],
    redEvents: [],
    traj: [{ m: 0, H: 66.1, D: 26.7, A: 7.1 }, { m: 1, H: 65.9, D: 27, A: 7.1 }, { m: 2, H: 65.6, D: 27.2, A: 7.2 }, { m: 3, H: 65.4, D: 27.4, A: 7.2 }, { m: 4, H: 65.1, D: 27.7, A: 7.2 }, { m: 5, H: 64.8, D: 27.9, A: 7.3 }, { m: 6, H: 64.6, D: 28.2, A: 7.3 }, { m: 7, H: 64.3, D: 28.4, A: 7.3 }, { m: 8, H: 64, D: 28.7, A: 7.3 }, { m: 9, H: 63.7, D: 28.9, A: 7.4 }, { m: 10, H: 63.4, D: 29.2, A: 7.4 }, { m: 11, H: 63.2, D: 29.4, A: 7.4 }, { m: 12, H: 62.9, D: 29.7, A: 7.4 }, { m: 13, H: 62.6, D: 30, A: 7.5 }, { m: 14, H: 62.3, D: 30.2, A: 7.5 }, { m: 15, H: 62, D: 30.5, A: 7.5 }, { m: 16, H: 61.6, D: 30.8, A: 7.6 }, { m: 17, H: 61.3, D: 31.1, A: 7.6 }, { m: 18, H: 61, D: 31.4, A: 7.6 }, { m: 19, H: 60.7, D: 31.7, A: 7.6 }, { m: 20, H: 60.4, D: 32, A: 7.7 }, { m: 21, H: 60, D: 32.3, A: 7.7 }, { m: 22, H: 59.7, D: 32.6, A: 7.7 }, { m: 23, H: 59.4, D: 32.9, A: 7.7 }, { m: 24, H: 59, D: 33.2, A: 7.8 }, { m: 25, H: 58.7, D: 33.5, A: 7.8 }, { m: 26, H: 58.3, D: 33.9, A: 7.8 }, { m: 27, H: 57.9, D: 34.2, A: 7.8 }, { m: 28, H: 57.6, D: 34.6, A: 7.9 }, { m: 29, H: 57.2, D: 34.9, A: 7.9 }, { m: 30, H: 56.8, D: 35.3, A: 7.9 }, { m: 31, H: 56.4, D: 35.6, A: 7.9 }, { m: 32, H: 56, D: 36, A: 8 }, { m: 33, H: 55.6, D: 36.4, A: 8 }, { m: 34, H: 55.2, D: 36.8, A: 8 }, { m: 35, H: 54.8, D: 37.2, A: 8 }, { m: 36, H: 54.4, D: 37.6, A: 8 }, { m: 37, H: 54, D: 38, A: 8 }, { m: 38, H: 53.5, D: 38.4, A: 8.1 }, { m: 39, H: 53.1, D: 38.8, A: 8.1 }, { m: 40, H: 52.6, D: 39.3, A: 8.1 }, { m: 41, H: 52.2, D: 39.7, A: 8.1 }, { m: 42, H: 51.7, D: 40.2, A: 8.1 }, { m: 43, H: 51.2, D: 40.6, A: 8.1 }, { m: 44, H: 50.7, D: 41.1, A: 8.1 }, { m: 45, H: 81.3, D: 17.3, A: 1.3 }, { m: 46, H: 81.3, D: 17.4, A: 1.3 }, { m: 47, H: 81.3, D: 17.4, A: 1.3 }, { m: 48, H: 81.4, D: 17.4, A: 1.2 }, { m: 49, H: 81.4, D: 17.4, A: 1.2 }, { m: 50, H: 81.4, D: 17.4, A: 1.2 }, { m: 51, H: 81.4, D: 17.4, A: 1.1 }, { m: 52, H: 81.4, D: 17.4, A: 1.1 }, { m: 53, H: 94, D: 5.9, A: 0.1 }, { m: 54, H: 94.1, D: 5.8, A: 0.1 }, { m: 55, H: 94.2, D: 5.7, A: 0.1 }, { m: 56, H: 94.3, D: 5.6, A: 0.1 }, { m: 57, H: 94.4, D: 5.5, A: 0.1 }, { m: 58, H: 94.5, D: 5.4, A: 0.1 }, { m: 59, H: 94.6, D: 5.3, A: 0.1 }, { m: 60, H: 94.7, D: 5.2, A: 0.1 }, { m: 61, H: 94.9, D: 5.1, A: 0.1 }, { m: 62, H: 95, D: 5, A: 0.1 }, { m: 63, H: 95.1, D: 4.8, A: 0.1 }, { m: 64, H: 95.3, D: 4.7, A: 0 }, { m: 65, H: 95.4, D: 4.6, A: 0 }, { m: 66, H: 95.5, D: 4.4, A: 0 }, { m: 67, H: 95.7, D: 4.3, A: 0 }, { m: 68, H: 95.8, D: 4.1, A: 0 }, { m: 69, H: 96, D: 4, A: 0 }, { m: 70, H: 96.1, D: 3.8, A: 0 }, { m: 71, H: 96.3, D: 3.7, A: 0 }, { m: 72, H: 96.5, D: 3.5, A: 0 }, { m: 73, H: 96.7, D: 3.3, A: 0 }, { m: 74, H: 99.4, D: 0.6, A: 0 }, { m: 75, H: 99.5, D: 0.5, A: 0 }, { m: 76, H: 99.5, D: 0.5, A: 0 }, { m: 77, H: 99.6, D: 0.4, A: 0 }, { m: 78, H: 99.6, D: 0.4, A: 0 }, { m: 79, H: 99.7, D: 0.3, A: 0 }, { m: 80, H: 99.7, D: 0.3, A: 0 }, { m: 81, H: 99.8, D: 0.2, A: 0 }, { m: 82, H: 99.8, D: 0.2, A: 0 }, { m: 83, H: 99.8, D: 0.2, A: 0 }, { m: 84, H: 99.9, D: 0.1, A: 0 }, { m: 85, H: 99.9, D: 0.1, A: 0 }, { m: 86, H: 99.9, D: 0.1, A: 0 }, { m: 87, H: 100, D: 0, A: 0 }, { m: 88, H: 100, D: 0, A: 0 }, { m: 89, H: 100, D: 0, A: 0 }, { m: 90, H: 100, D: 0, A: 0 }],
  },
  {
    fid: 1489418,
    home: "Algeria",
    away: "Austria",
    eloHome: 1785,
    eloAway: 1836,
    finalScore: "3-3",
    goalEvents: [{ m: 28, score: "0-1" }, { m: 45, score: "1-1" }, { m: 55, score: "1-2" }, { m: 60, score: "2-2" }, { m: 90, score: "3-3" }],
    redEvents: [],
    traj: [{ m: 0, H: 30.5, D: 36.4, A: 33.1 }, { m: 1, H: 30.4, D: 36.6, A: 32.9 }, { m: 2, H: 30.4, D: 36.8, A: 32.8 }, { m: 3, H: 30.3, D: 37, A: 32.7 }, { m: 4, H: 30.2, D: 37.3, A: 32.5 }, { m: 5, H: 30.2, D: 37.5, A: 32.4 }, { m: 6, H: 30.1, D: 37.7, A: 32.2 }, { m: 7, H: 30, D: 37.9, A: 32.1 }, { m: 8, H: 29.9, D: 38.2, A: 31.9 }, { m: 9, H: 29.8, D: 38.4, A: 31.8 }, { m: 10, H: 29.8, D: 38.6, A: 31.6 }, { m: 11, H: 29.7, D: 38.9, A: 31.5 }, { m: 12, H: 29.6, D: 39.1, A: 31.3 }, { m: 13, H: 29.5, D: 39.4, A: 31.1 }, { m: 14, H: 29.4, D: 39.6, A: 31 }, { m: 15, H: 29.3, D: 39.9, A: 30.8 }, { m: 16, H: 29.2, D: 40.1, A: 30.7 }, { m: 17, H: 29.1, D: 40.4, A: 30.5 }, { m: 18, H: 29, D: 40.7, A: 30.4 }, { m: 19, H: 28.9, D: 40.9, A: 30.2 }, { m: 20, H: 28.8, D: 41.2, A: 30 }, { m: 21, H: 28.7, D: 41.5, A: 29.9 }, { m: 22, H: 28.5, D: 41.8, A: 29.7 }, { m: 23, H: 28.4, D: 42, A: 29.5 }, { m: 24, H: 28.3, D: 42.3, A: 29.4 }, { m: 25, H: 28.2, D: 42.6, A: 29.2 }, { m: 26, H: 28, D: 42.9, A: 29 }, { m: 27, H: 27.9, D: 43.2, A: 28.9 }, { m: 28, H: 9.5, D: 26.6, A: 63.9 }, { m: 29, H: 9.3, D: 26.7, A: 64 }, { m: 30, H: 9.2, D: 26.7, A: 64.2 }, { m: 31, H: 9, D: 26.7, A: 64.3 }, { m: 32, H: 8.8, D: 26.7, A: 64.4 }, { m: 33, H: 8.7, D: 26.7, A: 64.6 }, { m: 34, H: 8.5, D: 26.8, A: 64.7 }, { m: 35, H: 8.4, D: 26.8, A: 64.9 }, { m: 36, H: 8.2, D: 26.8, A: 65.1 }, { m: 37, H: 8, D: 26.8, A: 65.2 }, { m: 38, H: 7.9, D: 26.8, A: 65.4 }, { m: 39, H: 7.7, D: 26.7, A: 65.6 }, { m: 40, H: 7.5, D: 26.7, A: 65.8 }, { m: 41, H: 7.3, D: 26.7, A: 66 }, { m: 42, H: 7.2, D: 26.7, A: 66.2 }, { m: 43, H: 7, D: 26.6, A: 66.4 }, { m: 44, H: 6.8, D: 26.6, A: 66.6 }, { m: 45, H: 24.8, D: 49.8, A: 25.4 }, { m: 46, H: 24.6, D: 50.2, A: 25.2 }, { m: 47, H: 24.4, D: 50.7, A: 25 }, { m: 48, H: 24.1, D: 51.1, A: 24.7 }, { m: 49, H: 23.9, D: 51.6, A: 24.5 }, { m: 50, H: 23.6, D: 52.1, A: 24.3 }, { m: 51, H: 23.4, D: 52.6, A: 24 }, { m: 52, H: 23.1, D: 53.1, A: 23.8 }, { m: 53, H: 22.9, D: 53.6, A: 23.5 }, { m: 54, H: 22.6, D: 54.1, A: 23.3 }, { m: 55, H: 4.9, D: 25.6, A: 69.5 }, { m: 56, H: 4.7, D: 25.5, A: 69.8 }, { m: 57, H: 4.5, D: 25.3, A: 70.2 }, { m: 58, H: 4.3, D: 25.2, A: 70.5 }, { m: 59, H: 4.1, D: 25, A: 70.9 }, { m: 60, H: 20.8, D: 57.6, A: 21.6 }, { m: 61, H: 20.4, D: 58.2, A: 21.3 }, { m: 62, H: 20.1, D: 58.9, A: 21 }, { m: 63, H: 19.7, D: 59.6, A: 20.7 }, { m: 64, H: 19.3, D: 60.3, A: 20.4 }, { m: 65, H: 19, D: 61, A: 20 }, { m: 66, H: 18.6, D: 61.8, A: 19.7 }, { m: 67, H: 18.1, D: 62.5, A: 19.3 }, { m: 68, H: 17.7, D: 63.3, A: 19 }, { m: 69, H: 17.3, D: 64.2, A: 18.6 }, { m: 70, H: 16.8, D: 65, A: 18.2 }, { m: 71, H: 16.3, D: 65.9, A: 17.8 }, { m: 72, H: 15.9, D: 66.8, A: 17.3 }, { m: 73, H: 15.3, D: 67.8, A: 16.9 }, { m: 74, H: 14.8, D: 68.8, A: 16.4 }, { m: 75, H: 14.3, D: 69.8, A: 15.9 }, { m: 76, H: 13.7, D: 70.9, A: 15.4 }, { m: 77, H: 13.1, D: 72.1, A: 14.8 }, { m: 78, H: 12.5, D: 73.3, A: 14.3 }, { m: 79, H: 11.8, D: 74.5, A: 13.7 }, { m: 80, H: 11.1, D: 75.9, A: 13 }, { m: 81, H: 10.4, D: 77.3, A: 12.3 }, { m: 82, H: 9.6, D: 78.8, A: 11.6 }, { m: 83, H: 8.8, D: 80.5, A: 10.8 }, { m: 84, H: 7.9, D: 82.2, A: 9.9 }, { m: 85, H: 6.9, D: 84.1, A: 9 }, { m: 86, H: 5.9, D: 86.2, A: 7.9 }, { m: 87, H: 4.8, D: 88.5, A: 6.7 }, { m: 88, H: 3.5, D: 91.3, A: 5.2 }, { m: 89, H: 2.1, D: 94.5, A: 3.4 }, { m: 90, H: 0, D: 100, A: 0 }],
  },
  {
    fid: 1489395,
    home: "Belgium",
    away: "Iran",
    eloHome: 1879,
    eloAway: 1756,
    finalScore: "0-0",
    goalEvents: [],
    redEvents: [{ m: 66, side: "home" }],
    traj: [{ m: 0, H: 44.5, D: 35.2, A: 20.3 }, { m: 1, H: 44.3, D: 35.4, A: 20.3 }, { m: 2, H: 44.2, D: 35.6, A: 20.2 }, { m: 3, H: 44, D: 35.8, A: 20.2 }, { m: 4, H: 43.8, D: 36, A: 20.1 }, { m: 5, H: 43.7, D: 36.2, A: 20.1 }, { m: 6, H: 43.5, D: 36.4, A: 20 }, { m: 7, H: 43.3, D: 36.7, A: 20 }, { m: 8, H: 43.2, D: 36.9, A: 19.9 }, { m: 9, H: 43, D: 37.1, A: 19.9 }, { m: 10, H: 42.8, D: 37.4, A: 19.8 }, { m: 11, H: 42.6, D: 37.6, A: 19.8 }, { m: 12, H: 42.5, D: 37.8, A: 19.7 }, { m: 13, H: 42.3, D: 38.1, A: 19.6 }, { m: 14, H: 42.1, D: 38.3, A: 19.6 }, { m: 15, H: 41.9, D: 38.6, A: 19.5 }, { m: 16, H: 41.7, D: 38.8, A: 19.5 }, { m: 17, H: 41.5, D: 39.1, A: 19.4 }, { m: 18, H: 41.3, D: 39.4, A: 19.3 }, { m: 19, H: 41.1, D: 39.6, A: 19.3 }, { m: 20, H: 40.9, D: 39.9, A: 19.2 }, { m: 21, H: 40.7, D: 40.2, A: 19.2 }, { m: 22, H: 40.5, D: 40.4, A: 19.1 }, { m: 23, H: 40.2, D: 40.7, A: 19 }, { m: 24, H: 40, D: 41, A: 19 }, { m: 25, H: 39.8, D: 41.3, A: 18.9 }, { m: 26, H: 39.6, D: 41.6, A: 18.8 }, { m: 27, H: 39.3, D: 41.9, A: 18.8 }, { m: 28, H: 39.1, D: 42.2, A: 18.7 }, { m: 29, H: 38.8, D: 42.6, A: 18.6 }, { m: 30, H: 38.6, D: 42.9, A: 18.5 }, { m: 31, H: 38.3, D: 43.2, A: 18.5 }, { m: 32, H: 38.1, D: 43.5, A: 18.4 }, { m: 33, H: 37.8, D: 43.9, A: 18.3 }, { m: 34, H: 37.5, D: 44.2, A: 18.2 }, { m: 35, H: 37.3, D: 44.6, A: 18.1 }, { m: 36, H: 37, D: 44.9, A: 18.1 }, { m: 37, H: 36.7, D: 45.3, A: 18 }, { m: 38, H: 36.4, D: 45.7, A: 17.9 }, { m: 39, H: 36.1, D: 46.1, A: 17.8 }, { m: 40, H: 35.8, D: 46.5, A: 17.7 }, { m: 41, H: 35.5, D: 46.9, A: 17.6 }, { m: 42, H: 35.2, D: 47.3, A: 17.5 }, { m: 43, H: 34.9, D: 47.7, A: 17.4 }, { m: 44, H: 34.6, D: 48.1, A: 17.3 }, { m: 45, H: 34.2, D: 48.6, A: 17.2 }, { m: 46, H: 33.9, D: 49, A: 17.1 }, { m: 47, H: 33.5, D: 49.5, A: 17 }, { m: 48, H: 33.2, D: 49.9, A: 16.9 }, { m: 49, H: 32.8, D: 50.4, A: 16.8 }, { m: 50, H: 32.5, D: 50.9, A: 16.6 }, { m: 51, H: 32.1, D: 51.4, A: 16.5 }, { m: 52, H: 31.7, D: 51.9, A: 16.4 }, { m: 53, H: 31.3, D: 52.4, A: 16.3 }, { m: 54, H: 30.9, D: 53, A: 16.1 }, { m: 55, H: 30.5, D: 53.5, A: 16 }, { m: 56, H: 30, D: 54.1, A: 15.8 }, { m: 57, H: 29.6, D: 54.7, A: 15.7 }, { m: 58, H: 29.1, D: 55.3, A: 15.5 }, { m: 59, H: 28.7, D: 55.9, A: 15.4 }, { m: 60, H: 28.2, D: 56.6, A: 15.2 }, { m: 61, H: 27.7, D: 57.2, A: 15 }, { m: 62, H: 27.2, D: 57.9, A: 14.9 }, { m: 63, H: 26.7, D: 58.6, A: 14.7 }, { m: 64, H: 26.2, D: 59.3, A: 14.5 }, { m: 65, H: 25.6, D: 60.1, A: 14.3 }, { m: 66, H: 23.9, D: 61.3, A: 14.8 }, { m: 67, H: 23.3, D: 62.1, A: 14.6 }, { m: 68, H: 22.8, D: 62.9, A: 14.3 }, { m: 69, H: 22.2, D: 63.7, A: 14.1 }, { m: 70, H: 21.6, D: 64.6, A: 13.8 }, { m: 71, H: 20.9, D: 65.5, A: 13.5 }, { m: 72, H: 20.3, D: 66.5, A: 13.2 }, { m: 73, H: 19.6, D: 67.5, A: 12.9 }, { m: 74, H: 18.9, D: 68.5, A: 12.6 }, { m: 75, H: 18.2, D: 69.6, A: 12.2 }, { m: 76, H: 17.5, D: 70.7, A: 11.8 }, { m: 77, H: 16.7, D: 71.9, A: 11.4 }, { m: 78, H: 15.9, D: 73.1, A: 11 }, { m: 79, H: 15, D: 74.4, A: 10.6 }, { m: 80, H: 14.1, D: 75.8, A: 10.1 }, { m: 81, H: 13.2, D: 77.2, A: 9.6 }, { m: 82, H: 12.2, D: 78.8, A: 9 }, { m: 83, H: 11.1, D: 80.5, A: 8.4 }, { m: 84, H: 10, D: 82.2, A: 7.8 }, { m: 85, H: 8.8, D: 84.2, A: 7 }, { m: 86, H: 7.5, D: 86.3, A: 6.2 }, { m: 87, H: 6.1, D: 88.7, A: 5.2 }, { m: 88, H: 4.5, D: 91.4, A: 4.1 }, { m: 89, H: 2.6, D: 94.7, A: 2.7 }, { m: 90, H: 0, D: 100, A: 0 }],
  },
  {
    fid: 1539074,
    home: "Senegal",
    away: "Iraq",
    eloHome: 1817,
    eloAway: 1586,
    finalScore: "5-0",
    goalEvents: [{ m: 4, score: "1-0" }, { m: 56, score: "2-0" }, { m: 59, score: "3-0" }, { m: 71, score: "4-0" }, { m: 82, score: "5-0" }],
    redEvents: [{ m: 13, side: "away" }],
    traj: [{ m: 0, H: 53.7, D: 32.5, A: 13.8 }, { m: 1, H: 53.5, D: 32.7, A: 13.8 }, { m: 2, H: 53.3, D: 32.9, A: 13.8 }, { m: 3, H: 53.1, D: 33.1, A: 13.8 }, { m: 4, H: 75, D: 20, A: 5 }, { m: 5, H: 75, D: 20.1, A: 4.9 }, { m: 6, H: 75, D: 20.2, A: 4.9 }, { m: 7, H: 74.9, D: 20.2, A: 4.8 }, { m: 8, H: 74.9, D: 20.3, A: 4.8 }, { m: 9, H: 74.9, D: 20.4, A: 4.7 }, { m: 10, H: 74.9, D: 20.4, A: 4.7 }, { m: 11, H: 74.9, D: 20.5, A: 4.6 }, { m: 12, H: 74.9, D: 20.6, A: 4.6 }, { m: 13, H: 76.4, D: 19.7, A: 4 }, { m: 14, H: 76.4, D: 19.7, A: 3.9 }, { m: 15, H: 76.3, D: 19.8, A: 3.9 }, { m: 16, H: 76.3, D: 19.9, A: 3.8 }, { m: 17, H: 76.3, D: 19.9, A: 3.8 }, { m: 18, H: 76.3, D: 20, A: 3.7 }, { m: 19, H: 76.3, D: 20, A: 3.7 }, { m: 20, H: 76.2, D: 20.1, A: 3.7 }, { m: 21, H: 76.2, D: 20.2, A: 3.6 }, { m: 22, H: 76.2, D: 20.2, A: 3.6 }, { m: 23, H: 76.2, D: 20.3, A: 3.5 }, { m: 24, H: 76.2, D: 20.3, A: 3.5 }, { m: 25, H: 76.2, D: 20.4, A: 3.4 }, { m: 26, H: 76.2, D: 20.5, A: 3.4 }, { m: 27, H: 76.2, D: 20.5, A: 3.3 }, { m: 28, H: 76.2, D: 20.6, A: 3.3 }, { m: 29, H: 76.2, D: 20.6, A: 3.2 }, { m: 30, H: 76.2, D: 20.7, A: 3.2 }, { m: 31, H: 76.2, D: 20.7, A: 3.1 }, { m: 32, H: 76.2, D: 20.8, A: 3.1 }, { m: 33, H: 76.2, D: 20.8, A: 3 }, { m: 34, H: 76.2, D: 20.8, A: 2.9 }, { m: 35, H: 76.2, D: 20.9, A: 2.9 }, { m: 36, H: 76.3, D: 20.9, A: 2.8 }, { m: 37, H: 76.3, D: 20.9, A: 2.8 }, { m: 38, H: 76.3, D: 21, A: 2.7 }, { m: 39, H: 76.3, D: 21, A: 2.7 }, { m: 40, H: 76.4, D: 21, A: 2.6 }, { m: 41, H: 76.4, D: 21, A: 2.6 }, { m: 42, H: 76.4, D: 21.1, A: 2.5 }, { m: 43, H: 76.5, D: 21.1, A: 2.4 }, { m: 44, H: 76.5, D: 21.1, A: 2.4 }, { m: 45, H: 76.6, D: 21.1, A: 2.3 }, { m: 46, H: 76.7, D: 21.1, A: 2.3 }, { m: 47, H: 76.7, D: 21.1, A: 2.2 }, { m: 48, H: 76.8, D: 21.1, A: 2.1 }, { m: 49, H: 76.9, D: 21, A: 2.1 }, { m: 50, H: 77, D: 21, A: 2 }, { m: 51, H: 77.1, D: 21, A: 1.9 }, { m: 52, H: 77.2, D: 21, A: 1.9 }, { m: 53, H: 77.3, D: 20.9, A: 1.8 }, { m: 54, H: 77.4, D: 20.9, A: 1.8 }, { m: 55, H: 77.5, D: 20.8, A: 1.7 }, { m: 56, H: 92.3, D: 7.5, A: 0.2 }, { m: 57, H: 92.5, D: 7.4, A: 0.2 }, { m: 58, H: 92.6, D: 7.2, A: 0.2 }, { m: 59, H: 97.8, D: 2.2, A: 0 }, { m: 60, H: 97.9, D: 2.1, A: 0 }, { m: 61, H: 98, D: 2, A: 0 }, { m: 62, H: 98.1, D: 1.9, A: 0 }, { m: 63, H: 98.2, D: 1.8, A: 0 }, { m: 64, H: 98.3, D: 1.7, A: 0 }, { m: 65, H: 98.4, D: 1.6, A: 0 }, { m: 66, H: 98.5, D: 1.5, A: 0 }, { m: 67, H: 98.5, D: 1.4, A: 0 }, { m: 68, H: 98.6, D: 1.4, A: 0 }, { m: 69, H: 98.7, D: 1.3, A: 0 }, { m: 70, H: 98.8, D: 1.2, A: 0 }, { m: 71, H: 99.8, D: 0.2, A: 0 }, { m: 72, H: 99.8, D: 0.2, A: 0 }, { m: 73, H: 99.8, D: 0.2, A: 0 }, { m: 74, H: 99.8, D: 0.2, A: 0 }, { m: 75, H: 99.9, D: 0.1, A: 0 }, { m: 76, H: 99.9, D: 0.1, A: 0 }, { m: 77, H: 99.9, D: 0.1, A: 0 }, { m: 78, H: 99.9, D: 0.1, A: 0 }, { m: 79, H: 99.9, D: 0.1, A: 0 }, { m: 80, H: 99.9, D: 0.1, A: 0 }, { m: 81, H: 100, D: 0, A: 0 }, { m: 82, H: 100, D: 0, A: 0 }, { m: 83, H: 100, D: 0, A: 0 }, { m: 84, H: 100, D: 0, A: 0 }, { m: 85, H: 100, D: 0, A: 0 }, { m: 86, H: 100, D: 0, A: 0 }, { m: 87, H: 100, D: 0, A: 0 }, { m: 88, H: 100, D: 0, A: 0 }, { m: 89, H: 100, D: 0, A: 0 }, { m: 90, H: 100, D: 0, A: 0 }],
  },
  {
    fid: 1489401,
    home: "Norway",
    away: "Senegal",
    eloHome: 1951,
    eloAway: 1817,
    finalScore: "3-2",
    goalEvents: [{ m: 43, score: "1-0" }, { m: 48, score: "2-0" }, { m: 53, score: "2-1" }, { m: 58, score: "3-1" }, { m: 90, score: "3-2" }],
    redEvents: [],
    traj: [{ m: 0, H: 45.4, D: 35, A: 19.6 }, { m: 1, H: 45.3, D: 35.2, A: 19.6 }, { m: 2, H: 45.1, D: 35.4, A: 19.5 }, { m: 3, H: 44.9, D: 35.6, A: 19.5 }, { m: 4, H: 44.8, D: 35.8, A: 19.4 }, { m: 5, H: 44.6, D: 36, A: 19.4 }, { m: 6, H: 44.4, D: 36.2, A: 19.3 }, { m: 7, H: 44.2, D: 36.5, A: 19.3 }, { m: 8, H: 44.1, D: 36.7, A: 19.2 }, { m: 9, H: 43.9, D: 36.9, A: 19.2 }, { m: 10, H: 43.7, D: 37.2, A: 19.1 }, { m: 11, H: 43.5, D: 37.4, A: 19.1 }, { m: 12, H: 43.3, D: 37.6, A: 19 }, { m: 13, H: 43.1, D: 37.9, A: 19 }, { m: 14, H: 42.9, D: 38.1, A: 18.9 }, { m: 15, H: 42.7, D: 38.4, A: 18.9 }, { m: 16, H: 42.5, D: 38.6, A: 18.8 }, { m: 17, H: 42.3, D: 38.9, A: 18.8 }, { m: 18, H: 42.1, D: 39.2, A: 18.7 }, { m: 19, H: 41.9, D: 39.4, A: 18.7 }, { m: 20, H: 41.7, D: 39.7, A: 18.6 }, { m: 21, H: 41.5, D: 40, A: 18.6 }, { m: 22, H: 41.3, D: 40.2, A: 18.5 }, { m: 23, H: 41, D: 40.5, A: 18.4 }, { m: 24, H: 40.8, D: 40.8, A: 18.4 }, { m: 25, H: 40.6, D: 41.1, A: 18.3 }, { m: 26, H: 40.3, D: 41.4, A: 18.2 }, { m: 27, H: 40.1, D: 41.7, A: 18.2 }, { m: 28, H: 39.8, D: 42, A: 18.1 }, { m: 29, H: 39.6, D: 42.4, A: 18 }, { m: 30, H: 39.3, D: 42.7, A: 18 }, { m: 31, H: 39.1, D: 43, A: 17.9 }, { m: 32, H: 38.8, D: 43.3, A: 17.8 }, { m: 33, H: 38.5, D: 43.7, A: 17.8 }, { m: 34, H: 38.3, D: 44, A: 17.7 }, { m: 35, H: 38, D: 44.4, A: 17.6 }, { m: 36, H: 37.7, D: 44.8, A: 17.5 }, { m: 37, H: 37.4, D: 45.1, A: 17.5 }, { m: 38, H: 37.1, D: 45.5, A: 17.4 }, { m: 39, H: 36.8, D: 45.9, A: 17.3 }, { m: 40, H: 36.5, D: 46.3, A: 17.2 }, { m: 41, H: 36.2, D: 46.7, A: 17.1 }, { m: 42, H: 35.9, D: 47.1, A: 17 }, { m: 43, H: 71.1, D: 24.9, A: 4 }, { m: 44, H: 71.3, D: 24.9, A: 3.9 }, { m: 45, H: 71.4, D: 24.8, A: 3.8 }, { m: 46, H: 71.5, D: 24.8, A: 3.7 }, { m: 47, H: 71.7, D: 24.8, A: 3.6 }, { m: 48, H: 88.4, D: 11, A: 0.6 }, { m: 49, H: 88.6, D: 10.9, A: 0.5 }, { m: 50, H: 88.8, D: 10.7, A: 0.5 }, { m: 51, H: 89, D: 10.5, A: 0.5 }, { m: 52, H: 89.2, D: 10.4, A: 0.5 }, { m: 53, H: 72.7, D: 24.4, A: 2.9 }, { m: 54, H: 72.9, D: 24.3, A: 2.8 }, { m: 55, H: 73.1, D: 24.2, A: 2.7 }, { m: 56, H: 73.3, D: 24.1, A: 2.6 }, { m: 57, H: 73.6, D: 24, A: 2.5 }, { m: 58, H: 90.5, D: 9.2, A: 0.3 }, { m: 59, H: 90.7, D: 9, A: 0.3 }, { m: 60, H: 90.9, D: 8.8, A: 0.3 }, { m: 61, H: 91.2, D: 8.6, A: 0.2 }, { m: 62, H: 91.4, D: 8.3, A: 0.2 }, { m: 63, H: 91.7, D: 8.1, A: 0.2 }, { m: 64, H: 91.9, D: 7.9, A: 0.2 }, { m: 65, H: 92.2, D: 7.6, A: 0.2 }, { m: 66, H: 92.5, D: 7.4, A: 0.1 }, { m: 67, H: 92.7, D: 7.1, A: 0.1 }, { m: 68, H: 93, D: 6.9, A: 0.1 }, { m: 69, H: 93.3, D: 6.6, A: 0.1 }, { m: 70, H: 93.6, D: 6.3, A: 0.1 }, { m: 71, H: 93.9, D: 6, A: 0.1 }, { m: 72, H: 94.2, D: 5.7, A: 0.1 }, { m: 73, H: 94.5, D: 5.4, A: 0.1 }, { m: 74, H: 94.8, D: 5.1, A: 0 }, { m: 75, H: 95.1, D: 4.8, A: 0 }, { m: 76, H: 95.4, D: 4.5, A: 0 }, { m: 77, H: 95.8, D: 4.2, A: 0 }, { m: 78, H: 96.1, D: 3.9, A: 0 }, { m: 79, H: 96.4, D: 3.5, A: 0 }, { m: 80, H: 96.8, D: 3.2, A: 0 }, { m: 81, H: 97.1, D: 2.9, A: 0 }, { m: 82, H: 97.5, D: 2.5, A: 0 }, { m: 83, H: 97.8, D: 2.2, A: 0 }, { m: 84, H: 98.2, D: 1.8, A: 0 }, { m: 85, H: 98.5, D: 1.5, A: 0 }, { m: 86, H: 98.8, D: 1.2, A: 0 }, { m: 87, H: 99.2, D: 0.8, A: 0 }, { m: 88, H: 99.5, D: 0.5, A: 0 }, { m: 89, H: 99.8, D: 0.2, A: 0 }, { m: 90, H: 100, D: 0, A: 0 }],
  },
  {
    fid: 1565176,
    home: "Germany",
    away: "Paraguay",
    eloHome: 1916,
    eloAway: 1815,
    finalScore: "1-1",
    goalEvents: [{ m: 42, score: "0-1" }, { m: 54, score: "1-1" }],
    redEvents: [],
    traj: [{ m: 0, H: 42.6, D: 35.5, A: 21.8 }, { m: 1, H: 42.5, D: 35.7, A: 21.8 }, { m: 2, H: 42.3, D: 36, A: 21.7 }, { m: 3, H: 42.2, D: 36.2, A: 21.6 }, { m: 4, H: 42, D: 36.4, A: 21.6 }, { m: 5, H: 41.9, D: 36.6, A: 21.5 }, { m: 6, H: 41.7, D: 36.8, A: 21.4 }, { m: 7, H: 41.6, D: 37, A: 21.4 }, { m: 8, H: 41.4, D: 37.3, A: 21.3 }, { m: 9, H: 41.3, D: 37.5, A: 21.3 }, { m: 10, H: 41.1, D: 37.7, A: 21.2 }, { m: 11, H: 40.9, D: 38, A: 21.1 }, { m: 12, H: 40.7, D: 38.2, A: 21 }, { m: 13, H: 40.6, D: 38.4, A: 21 }, { m: 14, H: 40.4, D: 38.7, A: 20.9 }, { m: 15, H: 40.2, D: 38.9, A: 20.8 }, { m: 16, H: 40, D: 39.2, A: 20.8 }, { m: 17, H: 39.8, D: 39.5, A: 20.7 }, { m: 18, H: 39.7, D: 39.7, A: 20.6 }, { m: 19, H: 39.5, D: 40, A: 20.6 }, { m: 20, H: 39.3, D: 40.3, A: 20.5 }, { m: 21, H: 39.1, D: 40.5, A: 20.4 }, { m: 22, H: 38.9, D: 40.8, A: 20.3 }, { m: 23, H: 38.7, D: 41.1, A: 20.2 }, { m: 24, H: 38.5, D: 41.4, A: 20.2 }, { m: 25, H: 38.2, D: 41.7, A: 20.1 }, { m: 26, H: 38, D: 42, A: 20 }, { m: 27, H: 37.8, D: 42.3, A: 19.9 }, { m: 28, H: 37.6, D: 42.6, A: 19.8 }, { m: 29, H: 37.3, D: 42.9, A: 19.8 }, { m: 30, H: 37.1, D: 43.2, A: 19.7 }, { m: 31, H: 36.9, D: 43.5, A: 19.6 }, { m: 32, H: 36.6, D: 43.9, A: 19.5 }, { m: 33, H: 36.4, D: 44.2, A: 19.4 }, { m: 34, H: 36.1, D: 44.6, A: 19.3 }, { m: 35, H: 35.9, D: 44.9, A: 19.2 }, { m: 36, H: 35.6, D: 45.3, A: 19.1 }, { m: 37, H: 35.3, D: 45.6, A: 19 }, { m: 38, H: 35.1, D: 46, A: 18.9 }, { m: 39, H: 34.8, D: 46.4, A: 18.8 }, { m: 40, H: 34.5, D: 46.8, A: 18.7 }, { m: 41, H: 34.2, D: 47.2, A: 18.6 }, { m: 42, H: 11.8, D: 30.9, A: 57.2 }, { m: 43, H: 11.5, D: 30.9, A: 57.5 }, { m: 44, H: 11.3, D: 30.9, A: 57.9 }, { m: 45, H: 11, D: 30.8, A: 58.2 }, { m: 46, H: 10.7, D: 30.8, A: 58.5 }, { m: 47, H: 10.4, D: 30.7, A: 58.9 }, { m: 48, H: 10.1, D: 30.7, A: 59.2 }, { m: 49, H: 9.8, D: 30.6, A: 59.6 }, { m: 50, H: 9.5, D: 30.5, A: 60 }, { m: 51, H: 9.2, D: 30.4, A: 60.4 }, { m: 52, H: 8.9, D: 30.3, A: 60.8 }, { m: 53, H: 8.6, D: 30.2, A: 61.2 }, { m: 54, H: 29.8, D: 53.3, A: 17 }, { m: 55, H: 29.4, D: 53.8, A: 16.8 }, { m: 56, H: 28.9, D: 54.4, A: 16.7 }, { m: 57, H: 28.5, D: 55, A: 16.5 }, { m: 58, H: 28.1, D: 55.6, A: 16.3 }, { m: 59, H: 27.7, D: 56.2, A: 16.1 }, { m: 60, H: 27.2, D: 56.8, A: 16 }, { m: 61, H: 26.7, D: 57.5, A: 15.8 }, { m: 62, H: 26.3, D: 58.2, A: 15.6 }, { m: 63, H: 25.8, D: 58.9, A: 15.4 }, { m: 64, H: 25.2, D: 59.6, A: 15.2 }, { m: 65, H: 24.7, D: 60.3, A: 15 }, { m: 66, H: 24.2, D: 61.1, A: 14.7 }, { m: 67, H: 23.6, D: 61.9, A: 14.5 }, { m: 68, H: 23.1, D: 62.7, A: 14.2 }, { m: 69, H: 22.5, D: 63.6, A: 14 }, { m: 70, H: 21.9, D: 64.4, A: 13.7 }, { m: 71, H: 21.2, D: 65.3, A: 13.4 }, { m: 72, H: 20.6, D: 66.3, A: 13.1 }, { m: 73, H: 19.9, D: 67.3, A: 12.8 }, { m: 74, H: 19.2, D: 68.3, A: 12.5 }, { m: 75, H: 18.5, D: 69.4, A: 12.1 }, { m: 76, H: 17.7, D: 70.5, A: 11.8 }, { m: 77, H: 16.9, D: 71.7, A: 11.4 }, { m: 78, H: 16.1, D: 72.9, A: 11 }, { m: 79, H: 15.2, D: 74.3, A: 10.5 }, { m: 80, H: 14.3, D: 75.6, A: 10.1 }, { m: 81, H: 13.4, D: 77.1, A: 9.5 }, { m: 82, H: 12.3, D: 78.7, A: 9 }, { m: 83, H: 11.3, D: 80.3, A: 8.4 }, { m: 84, H: 10.1, D: 82.1, A: 7.7 }, { m: 85, H: 8.9, D: 84.1, A: 7 }, { m: 86, H: 7.6, D: 86.2, A: 6.2 }, { m: 87, H: 6.2, D: 88.6, A: 5.2 }, { m: 88, H: 4.5, D: 91.4, A: 4.1 }, { m: 89, H: 2.7, D: 94.7, A: 2.7 }, { m: 90, H: 0, D: 100, A: 0 }],
  },
];

// ---------- Slide 6 — Results ----------
function S6Results() {
  // SIX real WC2026 matches, live P(H/D/A) produced by live_runner.py's trained
  // GoalProcessModel — see the MATCHES data block above. The presenter can click
  // between them live; nothing here is simulated or hand-tuned.
  const [selected, setSelected] = useState(0);
  const match = MATCHES[selected];
  const eloDiff = match.eloHome - match.eloAway;
  const kickoff = match.traj[0];

  const models = [
    { name: "M1 Scoreboard baseline", ll: "0.861", ac: "0.621", ece: "0.068", tone: "neutral" },
    { name: "M2 Gradient boosting (+Elo, uncalib.)", ll: "2.544", ac: "0.478", ece: "0.286", tone: "bad" },
    { name: "M3 Kairos (goal-process + market/Elo prior)", ll: "0.789", ac: "0.662", ece: "0.035", tone: "good" },
  ];

  const states = [
    { s: "All snapshots", n: "11,557", b: "0.861", k: "0.789", u: "+8.4%" },
    { s: "1-goal margin", n: "3,779", b: "0.856", k: "0.741", u: "+13.5%" },
    { s: "Has a red card", n: "806", b: "0.782", k: "0.795", u: "−1.7%" },
    { s: "Last 30 min · level", n: "1,458", b: "0.867", k: "0.846", u: "+2.4%" },
  ];

  return (
    <div className="flex flex-col gap-4 h-full">
      <Eyebrow>Results · World Cup 2026 track</Eyebrow>
      <H2>
        A team-strength-aware probability that <span style={{ color: ACCENT }}>reacts live.</span>
      </H2>

      <div className="grid grid-cols-5 gap-6 flex-1 min-h-0">
        <div
          className="col-span-3 p-4 flex flex-col"
          style={{ background: "#0F141B", border: "1px solid #1F2733" }}
        >
          <div
            className="uppercase tracking-[0.2em] mb-2"
            style={{ fontSize: 10, color: SUB, fontFamily: FONT_MONO }}
          >
            Live 1X2 trajectory · WC2026 · per-minute model output, out-of-sample (WC2026 is not in training data)
          </div>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {MATCHES.map((m, i) => {
              const isSel = i === selected;
              const code = (t: string) => TEAM_CODE[t] || t.slice(0, 3).toUpperCase();
              return (
                <button
                  key={m.fid}
                  onClick={() => setSelected(i)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 transition"
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    fontWeight: 600,
                    background: isSel ? ACCENT : "#0A0E14",
                    border: `1px solid ${isSel ? ACCENT : "#1F2733"}`,
                    color: isSel ? "#fff" : "#C9D1DA",
                    cursor: "pointer",
                  }}
                >
                  {code(m.home)} {m.finalScore} {code(m.away)}
                  {m.redEvents.length > 0 && (
                    <span style={{ color: isSel ? "#fff" : "#FF8A3D", fontSize: 8 }}>●</span>
                  )}
                </button>
              );
            })}
          </div>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={match.traj} margin={{ top: 26, right: 16, left: 0, bottom: 4 }}>
                <CartesianGrid stroke="#1F2733" />
                <XAxis
                  dataKey="m"
                  type="number"
                  domain={[0, 90]}
                  ticks={[0, 15, 30, 45, 60, 75, 90]}
                  stroke={SUB}
                  tick={{ fill: SUB, fontSize: 10 }}
                  label={{ value: "minute", position: "insideBottom", offset: -2, fill: SUB, fontSize: 10 }}
                />
                <YAxis stroke={SUB} tick={{ fill: SUB, fontSize: 10 }} domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ background: "#000", border: `1px solid ${ACCENT}` }} />
                {match.goalEvents.map((g) => (
                  <ReferenceLine
                    key={`g-${g.m}`}
                    x={g.m}
                    stroke={ACCENT}
                    strokeDasharray="3 3"
                    label={{ value: `${g.m}' ${g.score}`, fill: ACCENT, fontSize: 10, position: "top" }}
                  />
                ))}
                {match.redEvents.map((r) => (
                  <ReferenceLine
                    key={`r-${r.m}`}
                    x={r.m}
                    stroke="#FF8A3D"
                    strokeDasharray="2 2"
                    label={{ value: `${r.m}' RC`, fill: "#FF8A3D", fontSize: 10, position: "top" }}
                  />
                ))}
                <Line type="monotone" dataKey="H" stroke={ACCENT} strokeWidth={2.5} dot={false} name={`P(${match.home})`} />
                <Line type="monotone" dataKey="D" stroke="#FFB400" strokeWidth={2} dot={false} name="P(draw)" />
                <Line type="monotone" dataKey="A" stroke={ACCENT2} strokeWidth={2.5} dot={false} name={`P(${match.away})`} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-6 mt-2">
            <Legend2
              dot={ACCENT}
              label={`P(${match.home}) — kickoff ${kickoff.H}% from Elo ${eloDiff >= 0 ? "+" : ""}${eloDiff}`}
            />
            <Legend2 dot="#FFB400" label="P(draw)" />
            <Legend2 dot={ACCENT2} label={`P(${match.away})`} />
          </div>
        </div>

        <div className="col-span-2 flex flex-col gap-3 min-h-0">
          <div>
            <div
              className="uppercase tracking-[0.2em] px-3 pb-1"
              style={{ fontSize: 9, color: "#4C5867", fontFamily: FONT_MONO }}
            >
              Held-out test set — 127 matches · 11,557 snapshots
            </div>
            <div
              className="grid items-center px-3 py-2 uppercase tracking-[0.2em]"
              style={{ gridTemplateColumns: "1.7fr 0.7fr 0.6fr", fontSize: 9, color: SUB, borderBottom: "1px solid #1F2733" }}
            >
              <div>Model</div>
              <div className="text-right">Log-loss</div>
              <div className="text-right">Acc.</div>
            </div>
            {models.map((m) => (
              <div
                key={m.name}
                className="grid items-center px-3 py-2 tabular-nums"
                style={{ gridTemplateColumns: "1.7fr 0.7fr 0.6fr", borderBottom: "1px solid #1F2733", fontSize: 12 }}
              >
                <div style={{ fontWeight: 700, fontFamily: FONT_BODY }}>{m.name}</div>
                <div className="text-right" style={{ fontFamily: FONT_MONO, color: m.tone === "bad" ? ACCENT : m.tone === "good" ? ACCENT : "#fff", fontWeight: 700 }}>{m.ll}</div>
                <div className="text-right" style={{ fontFamily: FONT_MONO, color: SUB }}>{m.ac}</div>
              </div>
            ))}
          </div>
          <div
            className="p-2 text-center"
            style={{ background: "rgba(229,9,63,0.12)", border: `1px solid ${ACCENT}`, fontSize: 11, color: "#E6E9EE" }}
          >
            M2 memorised matches via a match-constant Elo feature — train acc 90.1% vs test 47.8%.
          </div>
          <div
            className="grid items-center px-3 py-2 uppercase tracking-[0.2em]"
            style={{ gridTemplateColumns: "1.5fr 0.7fr 0.7fr 0.8fr", fontSize: 9, color: SUB, borderBottom: "1px solid #1F2733" }}
          >
            <div>State</div>
            <div className="text-right">n</div>
            <div className="text-right">Base</div>
            <div className="text-right">Uplift</div>
          </div>
          {states.map((s) => (
            <div
              key={s.s}
              className="grid items-center px-3 py-2 tabular-nums"
              style={{
                gridTemplateColumns: "1.5fr 0.7fr 0.7fr 0.8fr",
                borderBottom: `1px solid #1F2733`,
                fontSize: 12,
              }}
            >
              <div style={{ fontWeight: 700, fontFamily: FONT_BODY }}>{s.s}</div>
              <div className="text-right" style={{ fontFamily: FONT_MONO, color: SUB }}>{s.n}</div>
              <div className="text-right" style={{ fontFamily: FONT_MONO, color: SUB }}>{s.b}</div>
              <div
                className="text-right"
                style={{
                  fontFamily: FONT_MONO,
                  color: s.u.startsWith("−") ? SUB : ACCENT,
                  fontWeight: 800,
                  fontSize: 14,
                }}
              >
                {s.u}
              </div>
            </div>
          ))}
        </div>
        <div
          className="uppercase tracking-[0.15em]"
          style={{ fontSize: 8.5, color: "#4C5867", fontFamily: FONT_MONO, marginTop: 2 }}
        >
          Red-card row is n=806 (~7% of test) — flipped sign for the third time across methodology fixes, not a stable read
        </div>
      </div>
    </div>
  );
}

// ---------- Slide 7 — Economic effect ----------
function S7Economics() {
  const scenarios = [
    { s: "Conservative", d: "0.10", v: "$50k", e: "$2.7M" },
    { s: "Base", d: "0.30", v: "$150k", e: "$2.7M", hi: true },
    { s: "Optimistic", d: "0.60", v: "$300k", e: "≈ $6M+" },
  ];
  return (
    <div className="flex flex-col gap-5 h-full">
      <Eyebrow>Economic effect</Eyebrow>
      <H1>
        Year-1 effect <span style={{ color: ACCENT }}>≈ $2.7M</span>
      </H1>
      <div style={{ fontSize: 16, lineHeight: 1.45, color: "#C9D1DA", maxWidth: 900 }}>
        Break-even needs only 0.06pp of hold uplift. Our WC2026-track evidence an edge
        exists: <strong style={{ color: ACCENT }}>+8.4% log-loss</strong> vs baseline
        overall, up to <strong style={{ color: ACCENT }}>+13.5%</strong> in
        one-goal-margin states — significant at p≈1.2×10⁻⁵ with the
        bootstrap CI excluding zero — turning that into a hold-uplift number
        is the job of the CLV backtest (see roadmap).
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div
          className="col-span-1 p-5 flex flex-col"
          style={{ background: "#000", border: `1px solid ${ACCENT}`, fontFamily: FONT_MONO }}
        >
          <div className="uppercase tracking-[0.2em]" style={{ fontSize: 10, color: SUB }}>
            The formula
          </div>
          <div style={{ fontSize: 15, lineHeight: 1.7, marginTop: 10 }}>
            <div>V = H · Δ</div>
            <div>L = α · V</div>
            <div style={{ color: ACCENT, fontWeight: 700 }}>
              E = N·L·t − C_dev − N·C_serve·t
            </div>
          </div>
          <div
            className="mt-3 pt-3"
            style={{ borderTop: "1px solid #1F2733", fontSize: 12, color: ACCENT2 }}
          >
            Break-even: Δ ≥ L / H = 0.06%
          </div>
          <div
            className="mt-3 pt-3 grid grid-cols-2 gap-x-3 gap-y-1"
            style={{ borderTop: "1px solid #1F2733", fontSize: 10.5, color: SUB, lineHeight: 1.5 }}
          >
            <div><span style={{ color: "#E6E9EE" }}>H</span> = handle staked</div>
            <div><span style={{ color: "#E6E9EE" }}>Δ</span> = hold uplift</div>
            <div><span style={{ color: "#E6E9EE" }}>V</span> = value to client</div>
            <div><span style={{ color: "#E6E9EE" }}>L</span> = our license fee</div>
            <div><span style={{ color: "#E6E9EE" }}>N, t</span> = clients, months</div>
            <div><span style={{ color: "#E6E9EE" }}>C_dev/serve</span> = our costs</div>
          </div>
        </div>

        <div className="col-span-2 grid grid-cols-2 gap-3 content-start">
          {[
            ["Handle H", "$50M / mo"],
            ["Uplift Δ", "0.30 pp"],
            ["Value V", "$150k / mo"],
            ["License L", "$30k / mo"],
            ["Clients N", "10"],
            ["Build C_dev", "$300k"],
            ["Serve C_serve", "$5k / client / mo"],
            ["Horizon t", "12 months"],
          ].map(([k, v]) => (
            <div
              key={k}
              className="px-4 py-3 flex items-center justify-between"
              style={{ background: "#0F141B", border: "1px solid #1F2733" }}
            >
              <div
                className="uppercase tracking-[0.2em]"
                style={{ fontSize: 10, color: SUB, fontFamily: FONT_MONO }}
              >
                {k}
              </div>
              <div className="tabular-nums" style={{ fontFamily: FONT_MONO, fontSize: 16, fontWeight: 600 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <div
          className="uppercase tracking-[0.2em] mb-2"
          style={{ fontSize: 11, color: SUB, fontFamily: FONT_MONO }}
        >
          Scenario range — one mid-size operator, 12 months
        </div>
        <div className="grid grid-cols-3 gap-4">
          {scenarios.map((s) => (
            <div
              key={s.s}
              className="px-5 py-4"
              style={{
                background: s.hi ? ACCENT : "#0F141B",
                border: `1px solid ${s.hi ? ACCENT : "#1F2733"}`,
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 700 }}>{s.s}</div>
              <div className="grid grid-cols-3 gap-2 mt-2 tabular-nums" style={{ fontFamily: FONT_MONO }}>
                <Sub label="Δ pp" v={s.d} />
                <Sub label="V/mo" v={s.v} />
                <Sub label="Year-1" v={s.e} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
function Sub({ label, v }: { label: string; v: string }) {
  return (
    <div>
      <div className="uppercase tracking-[0.2em]" style={{ fontSize: 9, opacity: 0.7 }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 800, marginTop: 2 }}>{v}</div>
    </div>
  );
}

// ---------- Slide 8 — Proven today + Roadmap (merged close) ----------
function S8Close() {
  const proven = [
    "Beats the scoreboard baseline on log-loss on every track tested — +8.1% club football with the market prior, +8.4% World Cup 2026 (p≈1.2×10⁻⁵, CI excludes zero, better in 91/127 held-out matches).",
    "Calibrated, not just ranked — ECE(home) 0.035 international, 0.036 club goal-process, vs 0.286 for the uncalibrated trap.",
    "Zero fabricated data, every source disclosed — including where a market prior was scraped, not licensed (Slide 5) — and the architecture matches the 2021-2026 literature and Opta's own described design.",
  ];
  const wk = [
    { w: "01", t: "CLV backtest", d: "Match live vs. closing odds — turns the log-loss edge into a € hold number; the serving path already ingests the comparison prices" },
    { w: "02", t: "Live service", d: "Wrap the model as a latency-budgeted API with health monitoring" },
    { w: "03", t: "Legalize the odds source", d: "616/636 matched (97%, incl. a betexplorer.com scrape against its ToS); move that path to the paid, ToS-compliant Odds API before any commercial use" },
    { w: "04", t: "Pilot kit", d: "Monitoring + A/B harness, then an operator-ready feed for a live client pilot" },
  ];
  return (
    <div className="flex flex-col gap-6 h-full">
      <Eyebrow>Proven today → Roadmap</Eyebrow>
      <H1>
        A measured edge — <span style={{ color: ACCENT }}>priced,</span> not promised.
      </H1>
      <div className="grid grid-cols-3 gap-4">
        {proven.map((d) => (
          <div
            key={d}
            className="p-4"
            style={{ background: "#0F141B", border: "1px solid #1F2733" }}
          >
            <div style={{ fontSize: 12.5, color: "#E6E9EE", lineHeight: 1.5 }}>{d}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-4 mt-auto">
        {wk.map((p, i) => (
          <div
            key={p.w}
            className="p-5 flex flex-col gap-3"
            style={{
              background: i === 0 ? ACCENT : "#0F141B",
              border: `1px solid ${i === 0 ? ACCENT : "#1F2733"}`,
              minHeight: 170,
            }}
          >
            <div
              className="tabular-nums"
              style={{ fontFamily: FONT_DISPLAY, fontSize: 38, fontWeight: 800, letterSpacing: 0 }}
            >
              {p.w}
            </div>
            <div style={{ fontSize: 16, fontWeight: 700, lineHeight: 1.2 }}>{p.t}</div>
            <div
              style={{
                fontSize: 11.5,
                color: i === 0 ? "rgba(255,255,255,0.85)" : SUB,
                lineHeight: 1.45,
                marginTop: "auto",
              }}
            >
              {p.d}
            </div>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between mt-2">
        <div style={{ fontSize: 14, color: SUB }}>
          <em>Kairos</em> — the opportune moment, priced.
        </div>
        <div
          className="px-4 py-2"
          style={{ background: ACCENT, fontSize: 12, fontWeight: 700, letterSpacing: 2, fontFamily: FONT_MONO }}
        >
          THANK YOU
        </div>
      </div>
    </div>
  );
}

// ---------- registry ----------
export const SLIDES: {
  eyebrow: string;
  Component: () => React.ReactElement;
  icon: any;
}[] = [
  { eyebrow: "Title", Component: S1Title, icon: Zap },
  { eyebrow: "Goal & market", Component: S2GoalMarket, icon: Target },
  { eyebrow: "Math + dualism", Component: S3MathDualism, icon: Activity },
  { eyebrow: "Research + model", Component: S4ResearchModel, icon: Layers },
  { eyebrow: "Dataset", Component: S5Dataset, icon: Database },
  { eyebrow: "Results", Component: S6Results, icon: TrendingUp },
  { eyebrow: "Economics", Component: S7Economics, icon: DollarSign },
  { eyebrow: "Close & roadmap", Component: S8Close, icon: AlertCircle },
];

export function Slide({ index }: { index: number }) {
  const total = SLIDES.length;
  const slide = SLIDES[index - 1];
  const Comp = slide.Component;
  return (
    <motion.div
      key={index}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="w-full h-full"
    >
      <SlideShell index={index} total={total} eyebrow={slide.eyebrow}>
        <Comp />
      </SlideShell>
    </motion.div>
  );
}
