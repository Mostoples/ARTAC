/* Prints a coarse ASCII luma map of an image so I can see the layout
   of a rendered frame without opening it. */
import { spawnSync } from "node:child_process";

const file = process.argv[2];
const cols = Number(process.argv[3] || 46);
const rows = Number(process.argv[4] || 40);

const r = spawnSync("ffmpeg", [
  "-v", "error", "-i", file,
  "-vf", `scale=${cols}:${rows},format=gray`,
  "-frames:v", "1", "-f", "rawvideo", "-",
], { encoding: "buffer", maxBuffer: 1 << 24 });

const px = r.stdout;
if (!px || px.length < cols * rows) {
  console.error("could not read pixels");
  process.exit(1);
}

const RAMP = " .:-=+*#%@";
for (let y = 0; y < rows; y++) {
  let line = "";
  for (let x = 0; x < cols; x++) {
    const v = px[y * cols + x];
    line += RAMP[Math.min(RAMP.length - 1, Math.floor((v / 255) * RAMP.length))];
  }
  console.log(line);
}
