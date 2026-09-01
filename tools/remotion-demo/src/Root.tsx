import React from "react";
import { Composition } from "remotion";
import { SyndicationDemo, INTRO_FRAMES, OUTRO_FRAMES } from "./SyndicationDemo";

const FPS = 25;
const SOURCE_VIDEO_FILE = "complete_syndication_demo_raw.mp4";
const SOURCE_VIDEO_DURATION_S = 218.12;
const VIDEO_FRAMES = Math.ceil(SOURCE_VIDEO_DURATION_S * FPS);

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="SyndicationDemo"
        component={SyndicationDemo}
        durationInFrames={INTRO_FRAMES + VIDEO_FRAMES + OUTRO_FRAMES}
        fps={FPS}
        width={1366}
        height={768}
        defaultProps={{
          videoFile: SOURCE_VIDEO_FILE,
          videoDurationInFrames: VIDEO_FRAMES,
        }}
      />
    </>
  );
};
