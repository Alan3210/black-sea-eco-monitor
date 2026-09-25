import { filterGroundStations } from "./groundStationFilters.js";
import { buildGroundStationLegend } from "./groundStationLegend.js";

export function buildGroundStationUiModel(
  stations = [],
  filters = {},
) {
  const visibleStations = filterGroundStations(
    stations,
    filters,
  );

  return {
    stations: visibleStations,
    legend: buildGroundStationLegend(
      visibleStations,
    ),
  };
}
