export function buildSourceOverview(sources = []) {
  return sources.map((source) => ({
    name: source.name || "Unknown source",
    type: source.type || "unknown",
    purpose: source.purpose || "",
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

export function renderSourceOverview(sources = []) {
  const groups = groupSourceOverview(sources);

  return Object.entries(groups)
    .map(([type, items]) => `
      <section class="source-group">
        <h3>${type}</h3>
        ${items.map((item) => `
          <div class="source-card">
            <strong>${item.name}</strong>
            <span>${item.purpose}</span>
          </div>
        `).join("")}
      </section>
    `)
    .join("");
}
