export function composeEvidencePanelContent(
  eventPayload = {},
  timelineHtml = "",
) {
  return `
    <div class="evidence-panel-event">
      <h3>Evidence Event</h3>
      <pre>${JSON.stringify(
        eventPayload || {},
        null,
        2,
      )}</pre>
    </div>

    ${timelineHtml}
  `;
}
