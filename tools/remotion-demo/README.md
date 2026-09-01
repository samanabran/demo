# Portal Syndication Demo — Remotion Wrapper

Wraps the real screen-recorded demo (from `../sgc_offplan_rental_property_management/tools/demo/`)
with an animated intro title card and a recap outro card.

## Prerequisites

```bash
npm install
```

## Usage

1. Record and build the raw narrated demo first (see the sibling `tools/demo/` README):
   ```bash
   cd ../sgc_offplan_rental_property_management/tools/demo
   python3 record_demo_complete.py --base http://localhost:18030
   python3 build_complete_video.py <session_id>
   ```
2. Copy the resulting `complete-demo-<session_id>-final.mp4` into `public/complete_syndication_demo_raw.mp4`
   (or update `SOURCE_VIDEO_FILE` in `src/Root.tsx` to point at a different filename).
3. Update `SOURCE_VIDEO_DURATION_S` in `src/Root.tsx` to match the new video's exact duration
   (`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 <file>`).
4. Render:
   ```bash
   npx remotion render src/index.ts SyndicationDemo out/final.mp4
   ```

## Editing the intro/outro

- `src/SyndicationDemo.tsx` — the `Intro` and `Outro` components (title cards, colors, copy).
- `src/Root.tsx` — composition timing: `FPS`, intro/outro frame counts, source video duration.

Colors/fonts are inline in `SyndicationDemo.tsx` (no external design system dependency) —
edit the `NAVY`/`GOLD`/`INK` constants at the top of that file to restyle.
