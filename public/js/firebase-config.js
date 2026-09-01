/* ============================================================
   ARTA-C — Firebase bootstrap
   These web keys are public by design; real access control
   lives in firestore.rules.
   ============================================================ */

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getAuth,
  setPersistence,
  browserLocalPersistence,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import {
  getFirestore,
  enableIndexedDbPersistence,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

export const firebaseConfig = {
  apiKey: "AIzaSyCiLcLtS3wjL6QJkt9oJyFJIOibKIWskDo",
  authDomain: "arta-id.firebaseapp.com",
  projectId: "arta-id",
  storageBucket: "arta-id.firebasestorage.app",
  messagingSenderId: "646541033392",
  appId: "1:646541033392:web:0db874a200a981e6d8e075",
};

/** true when the config still holds template values */
export const isPlaceholderConfig =
  firebaseConfig.apiKey.includes("REPLACE_WITH");

const DEMO_KEY = "artac.demo";

/**
 * Local UI review mode: browses the interface against seeded
 * sample data in localStorage instead of Firestore. Toggled by
 * ?demo=1 / ?demo=0, or by the buttons on the sign-in screen.
 */
export const isDemoRequested = (() => {
  try {
    const q = new URLSearchParams(location.search);
    if (q.get("demo") === "1") localStorage.setItem(DEMO_KEY, "1");
    if (q.get("demo") === "0") localStorage.removeItem(DEMO_KEY);
    return localStorage.getItem(DEMO_KEY) === "1";
  } catch {
    return false;
  }
})();

/** Turns demo mode on or off, then reloads into the chosen backend. */
export function setDemoMode(on) {
  try {
    if (on) localStorage.setItem(DEMO_KEY, "1");
    else localStorage.removeItem(DEMO_KEY);
  } catch { /* storage blocked; fall back to the query flag below */ }
  const url = new URL(location.href);
  url.searchParams.set("demo", on ? "1" : "0");
  location.replace(url.toString());
}

export const useDemoBackend = isPlaceholderConfig || isDemoRequested;

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

setPersistence(auth, browserLocalPersistence).catch(() => {
  /* falls back to in-memory persistence, e.g. private browsing */
});

enableIndexedDbPersistence(db).catch(() => {
  /* multiple tabs open or unsupported browser: online-only mode */
});
