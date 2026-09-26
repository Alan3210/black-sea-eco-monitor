import {
  getEvidenceCardClass,
  getEvidenceStatusClass,
  EVIDENCE_PANEL_THEME,
} from "./evidencePanelStyles.js";

export function buildEvidencePanelLayout(blocks = {}) {
  return {
    rootClass: EVIDENCE_PANEL_THEME.root,
    cards: [
      {
        type: "sources",
        className: getEvidenceCardClass("sources"),
        data: blocks.sources || {},
      },
      {
        type: "quality",
        className: getEvidenceCardClass("quality"),
        data: blocks.quality || {},
      },
      {
        type: "timeline",
        className: getEvidenceCardClass("timeline"),
        data: blocks.timeline || {},
      },
      {
        type: "crosscheck",
        className: getEvidenceCardClass("crosscheck"),
        data: blocks.crosscheck || {},
      },
    ],
    statusClass: getEvidenceStatusClass(
      blocks.status || "ready",
    ),
  };
}
