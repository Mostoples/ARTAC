/* ============================================================
   ARTA-C — backend selector
   Picks the live Firebase implementation when real keys are
   present, otherwise the localStorage demo backend.
   ============================================================ */

import { useDemoBackend } from "./firebase-config.js";

const impl = useDemoBackend
  ? await import("./backend-demo.js")
  : await import("./backend-firebase.js");

export const isDemo = impl.isDemo;
export const {
  onAuth, signIn, signUp, signOutUser, updateProfile, listUsersByRole,
  watchPatients, watchPatient, createPatient, updatePatient, deletePatient,
  watchSchedules, saveSchedule, deleteSchedule,
  watchDevice, watchDevicesFor, updateDevice,
  watchDoseLogs, watchDoseLogsFor, addDoseLog, updateDoseLog,
  watchAlerts, watchAlertsFor, addAlert, resolveAlert,
  watchComplaints, watchComplaintsFor, addComplaint, respondComplaint,
  watchMessages, sendMessage,
  watchVot, watchVotFor, addVot, updateVot,
  resetDemo,
} = impl;
