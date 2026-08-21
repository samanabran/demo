import React from "react";
import {
  AbsoluteFill,
  Sequence,
  Video,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";

const NAVY = "#10182A";
const NAVY_RAISED = "#161F35";
const GOLD = "#D8A73D";
const INK = "#F3F1EA";
const INK_SOFT = "#A8AEBD";
const LINE = "#2A3348";

const fontStack =
  "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif";

export const INTRO_FRAMES = 120;
export const OUTRO_FRAMES = 180;

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: fontStack,
        fontSize: 22,
        letterSpacing: 4,
        textTransform: "uppercase",
        color: GOLD,
        display: "flex",
        alignItems: "center",
        gap: 14,
      }}
    >
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: GOLD,
          display: "inline-block",
        }}
      />
      {children}
    </div>
  );
}

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const eyebrowOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleSpring = spring({ frame, fps, config: { damping: 200 } });
  const titleY = interpolate(titleSpring, [0, 1], [24, 0]);
  const titleOpacity = interpolate(frame, [10, 28], [0, 1], {
    extrapolateRight: "clamp",
  });
  const subOpacity = interpolate(frame, [30, 48], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const chipsOpacity = interpolate(frame, [46, 64], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [INTRO_FRAMES - 18, INTRO_FRAMES],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const chips = ["Bayut", "Property Finder", "Dubizzle", "Sample Feed"];

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 140% at 15% 10%, ${NAVY_RAISED} 0%, ${NAVY} 60%)`,
        opacity: fadeOut,
        justifyContent: "center",
        padding: "0 140px",
      }}
    >
      <div style={{ opacity: eyebrowOpacity, marginBottom: 26 }}>
        <Eyebrow>SGC Property Management</Eyebrow>
      </div>
      <div
        style={{
          fontFamily: fontStack,
          fontSize: 76,
          fontWeight: 700,
          color: INK,
          lineHeight: 1.08,
          letterSpacing: -1,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          maxWidth: 1100,
        }}
      >
        Portal Syndication
        <br />
        Complete Walkthrough
      </div>
      <div
        style={{
          fontFamily: fontStack,
          fontSize: 28,
          color: INK_SOFT,
          marginTop: 28,
          opacity: subOpacity,
          maxWidth: 900,
        }}
      >
        Connectivity, publishing, lead capture, and feed ingestion — all
        live, all real.
      </div>
      <div
        style={{
          display: "flex",
          gap: 14,
          marginTop: 40,
          opacity: chipsOpacity,
        }}
      >
        {chips.map((c) => (
          <div
            key={c}
            style={{
              fontFamily: fontStack,
              fontSize: 18,
              color: INK,
              border: `1px solid ${LINE}`,
              borderRadius: 999,
              padding: "10px 22px",
              background: "rgba(255,255,255,0.03)",
            }}
          >
            {c}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const recap = [
  "RapidAPI connectivity — Bayut, Property Finder, Dubizzle",
  "Real listing published + public search + gated lead capture",
  "Website Inquiries smart-button gap, found and fixed",
  "Sample partner XML feed ingested via the scheduled job",
];

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleSpring = spring({ frame, fps, config: { damping: 200 } });
  const titleY = interpolate(titleSpring, [0, 1], [20, 0]);

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 140% at 85% 90%, ${NAVY_RAISED} 0%, ${NAVY} 60%)`,
        opacity: fadeIn,
        padding: "110px 140px",
      }}
    >
      <div style={{ marginBottom: 22 }}>
        <Eyebrow>Recap</Eyebrow>
      </div>
      <div
        style={{
          fontFamily: fontStack,
          fontSize: 52,
          fontWeight: 700,
          color: INK,
          letterSpacing: -0.5,
          transform: `translateY(${titleY}px)`,
          marginBottom: 34,
        }}
      >
        The full syndication loop
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        {recap.map((line, i) => {
          const start = 20 + i * 10;
          const o = interpolate(frame, [start, start + 16], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const x = interpolate(frame, [start, start + 16], [-16, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={line}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                opacity: o,
                transform: `translateX(${x}px)`,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: GOLD,
                  flex: "none",
                }}
              />
              <span
                style={{
                  fontFamily: fontStack,
                  fontSize: 26,
                  color: INK_SOFT,
                }}
              >
                {line}
              </span>
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          bottom: 90,
          left: 140,
          right: 140,
          borderTop: `1px solid ${LINE}`,
          paddingTop: 26,
          opacity: interpolate(frame, [70, 90], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div
          style={{
            fontFamily: "'Consolas', 'SF Mono', monospace",
            fontSize: 16,
            color: INK_SOFT,
            lineHeight: 1.8,
          }}
        >
          tools/demo/record_demo_complete.py — re-record this walkthrough
          <br />
          tools/demo/build_complete_video.py &lt;session_id&gt; — rebuild the
          narrated cut
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const SyndicationDemo: React.FC<{
  videoFile: string;
  videoDurationInFrames: number;
}> = ({ videoFile, videoDurationInFrames }) => {
  return (
    <AbsoluteFill style={{ background: NAVY }}>
      <Sequence durationInFrames={INTRO_FRAMES}>
        <Intro />
      </Sequence>
      <Sequence
        from={INTRO_FRAMES}
        durationInFrames={videoDurationInFrames}
      >
        <Video src={staticFile(videoFile)} />
      </Sequence>
      <Sequence from={INTRO_FRAMES + videoDurationInFrames}>
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};
