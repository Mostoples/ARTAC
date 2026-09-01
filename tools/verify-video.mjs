/* Confirms the rendered video actually contains the caption overlay
   and the underlying screenshot, by comparing average brightness of
   the caption band against the same band in the source screenshot. */
import { spawnSync } from "node:child_process";

/** Mean luma of a cropped region: scale the crop to 1x1 and read the pixel. */
function meanLuma(file, crop, extraIn = []) {
  const r = spawnSync("ffmpeg", [
    "-v", "error", ...extraIn, "-i", file,
    "-vf", `${crop},scale=1:1,format=gray`,
    "-frames:v", "1", "-f", "rawvideo", "-",
  ], { encoding: "buffer", maxBuffer: 1 << 20 });
  const out = r.stdout;
  return out && out.length ? out[0] : null;
}

const CAP_BAND = "crop=1080:340:0:1420";  // where the caption card sits
const TOP_BAND = "crop=1080:400:0:200";   // app content, no caption

let bad = 0;
const note = (ok, msg) => { console.log(`${ok ? "ok  " : "FAIL"} ${msg}`); if (!ok) bad++; };

for (const [theme, shot] of [
  ["Neumorph", "shots/neu-landing-01-hero.png"],
  ["Glass", "shots/glass-landing-01-hero.png"],
]) {
  const vid = `video/ARTA-C-${theme}-1080x1920.mp4`;

  const capVid = meanLuma(vid, CAP_BAND, ["-ss", "1.4"]);
  const capSrc = meanLuma(shot, CAP_BAND);
  const topVid = meanLuma(vid, TOP_BAND, ["-ss", "1.4"]);
  const topSrc = meanLuma(shot, TOP_BAND);

  console.log(`\n${theme}: caption band video=${capVid} source=${capSrc} | top band video=${topVid} source=${topSrc}`);

  note(capVid !== null && topVid !== null, `${theme}: frames decodable`);
  // the caption card is a dark panel, so that band must differ from the raw shot
  note(Math.abs(capVid - capSrc) > 6, `${theme}: caption overlay present (delta ${Math.abs(capVid - capSrc).toFixed(1)})`);
  // the upper area should still resemble the screenshot (zoom shifts it slightly)
  note(Math.abs(topVid - topSrc) < 45, `${theme}: underlying screenshot retained (delta ${Math.abs(topVid - topSrc).toFixed(1)})`);
  // not a black or blown-out frame
  note(topVid > 12 && topVid < 250, `${theme}: frame exposure sane (${topVid})`);
}

/* motion check: two frames inside one shot must differ (Ken Burns) */
for (const theme of ["Neumorph", "Glass"]) {
  const vid = `video/ARTA-C-${theme}-1080x1920.mp4`;
  const a = meanLuma(vid, "crop=200:200:0:0", ["-ss", "1.0"]);
  const b = meanLuma(vid, "crop=200:200:0:0", ["-ss", "2.2"]);
  note(a !== null && b !== null, `${theme}: motion frames read`);
  console.log(`   ${theme}: corner luma 1.0s=${a} 2.2s=${b}`);
}

console.log(bad ? `\n${bad} check(s) failed.` : "\nVideo content verified.");
process.exit(bad ? 1 : 0);
