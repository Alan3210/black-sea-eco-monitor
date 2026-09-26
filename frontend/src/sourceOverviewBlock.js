import { t } from './i18n.js';

export function buildSourceOverview(sources = []) {
  return sources.map((source) => ({
    name: source.name || "Unknown source",
    type: source.type || "unknown",
    typeKey: source.typeKey || null,
    purpose: source.purpose || "",
    purposeKey: source.purposeKey || null,
    status: source.status || "available",
  }));
}

export function groupSourceOverview(sources = []) {
  return buildSourceOverview(sources).reduce(
    (groups, source) => {
      const key = source.type;

      if (!groups[key]) {
        groups[key] = [];
      }

      groups[key].push(source);
      return groups;
    },
    {},
  );
}

export function renderSourceOverview(sources = [], currentLanguage = 'ru') {


  const groups = groupSourceOverview(sources);


  Object.entries(groups).forEach(([type, items]) => {
  const key = items[0]?.typeKey || `sources.${type.toLowerCase()}`;


});

  return Object.entries(groups)
    .map(([type, items]) => `
      <section class="source-group">
        
        <h3>${t(
          currentLanguage,
          items[0]?.typeKey || `sources.${type.toLowerCase()}`
        )}</h3>
        ${items.map((item) => `
          <div class="source-card">
            <strong>${item.name}</strong>
            <span>${t(
              currentLanguage,
              item.purposeKey || `sources.${item.purpose.toLowerCase()}`
            )}</span>
          </div>
        `).join("")}
      </section>
    `)
    .join("");
}
