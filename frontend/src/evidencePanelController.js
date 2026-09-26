import {
  fetchEvidenceForEvent,
} from "./evidencePanelApi.js";

import {
  updateEvidencePanelContent,
} from "./evidencePanelBinding.js";


import {
  appendEvidenceTimeline,
} from "./evidenceTimelineLiveMount.js";


export async function loadEvidenceForEvent(
  eventId,
  container,
  fetchImpl = fetch,
) {
  const data = await fetchEvidenceForEvent(
    eventId,
    fetchImpl,
  );

  updateEvidencePanelContent(
    container,
    appendEvidenceTimeline(
      "",
      data,
    ),
  );

  return data;
}