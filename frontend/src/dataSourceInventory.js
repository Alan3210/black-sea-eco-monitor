export function normalizeDataSource(source = {}) {
  return {
    id: source.id || null,
    name: source.name || "Unknown source",
    type: source.type || "unknown",
    purpose: source.purpose || "",
    status: source.status || "available",
  };
}

export function buildDataSourceInventory(sources = []) {
  return sources.map(normalizeDataSource);
}

export function groupDataSourcesByType(sources = []) {
  return buildDataSourceInventory(sources).reduce(
    (groups, source) => {
      const type = source.type;

      if (!groups[type]) {
        groups[type] = [];
      }

      groups[type].push(source);

      return groups;
    },
    {},
  );
}
