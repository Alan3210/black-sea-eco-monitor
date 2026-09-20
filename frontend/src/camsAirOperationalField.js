export const CAMS_FIELD_COLORS = Object.freeze([
  '#3157d5',
  '#2aa9e0',
  '#5fd3c7',
  '#f2c94c',
  '#eb5757',
]);


export function normalizeCamsOpacityPercent(
  value,
  fallback = 55,
) {
  if (
    value === null
    || value === undefined
    || value === ''
  ) {
    return fallback;
  }

  const numeric = Number(value);

  if (!Number.isFinite(numeric)) {
    return fallback;
  }

  return Math.min(
    90,
    Math.max(
      20,
      Math.round(numeric),
    ),
  );
}


export function camsAxisEdges(
  coordinates = [],
) {
  const values = coordinates.map(Number);

  if (!values.length) {
    return [];
  }

  if (values.length === 1) {
    return [
      values[0] - 0.05,
      values[0] + 0.05,
    ];
  }

  const edges = [
    values[0]
      - (values[1] - values[0]) / 2,
  ];

  for (
    let index = 0;
    index < values.length - 1;
    index += 1
  ) {
    edges.push(
      (
        values[index]
        + values[index + 1]
      ) / 2,
    );
  }

  edges.push(
    values.at(-1)
      + (
        values.at(-1)
        - values.at(-2)
      ) / 2,
  );

  return edges;
}


export function buildCamsAirCellGeoJSON(
  payload = {},
) {
  const latitudes =
    payload.grid?.latitudes ?? [];

  const longitudes =
    payload.grid?.longitudes ?? [];

  const values =
    payload.grid?.values ?? [];

  const latEdges =
    camsAxisEdges(latitudes);

  const lonEdges =
    camsAxisEdges(longitudes);

  const features = [];

  for (
    let y = 0;
    y < latitudes.length;
    y += 1
  ) {
    for (
      let x = 0;
      x < longitudes.length;
      x += 1
    ) {
      const value =
        Number(values?.[y]?.[x]);

      if (!Number.isFinite(value)) {
        continue;
      }

      features.push({
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [lonEdges[x], latEdges[y]],
            [lonEdges[x + 1], latEdges[y]],
            [lonEdges[x + 1], latEdges[y + 1]],
            [lonEdges[x], latEdges[y + 1]],
            [lonEdges[x], latEdges[y]],
          ]],
        },
        properties: {
          value,
          latitude:
            Number(latitudes[y]),
          longitude:
            Number(longitudes[x]),
        },
      });
    }
  }

  return {
    type: 'FeatureCollection',
    features,
  };
}


export function camsPercentile(
  values = [],
  percentile = 0.5,
) {
  const finite =
    values
      .map(Number)
      .filter(
        Number.isFinite,
      )
      .sort(
        (left, right) =>
          left - right,
      );

  if (!finite.length) {
    return null;
  }

  const q =
    Math.min(
      1,
      Math.max(
        0,
        Number(percentile),
      ),
    );

  const position =
    (finite.length - 1) * q;

  const lower =
    Math.floor(position);

  const upper =
    Math.ceil(position);

  if (lower === upper) {
    return finite[lower];
  }

  const weight =
    position - lower;

  return (
    finite[lower]
    * (1 - weight)
    + finite[upper]
    * weight
  );
}


export function camsFiniteFieldValues(
  payload = {},
) {
  return (
    payload.grid?.values
    ?? []
  )
    .flat()
    .map(Number)
    .filter(
      Number.isFinite,
    );
}


export function camsFieldStops(
  statistics = {},
) {
  const minimum =
    Number(statistics.min);

  const maximum =
    Number(statistics.max);

  if (
    !Number.isFinite(minimum)
    || !Number.isFinite(maximum)
  ) {
    return [
      0,
      10,
      25,
      50,
      100,
    ];
  }

  if (maximum <= minimum) {
    const delta =
      Math.max(
        Math.abs(minimum) * 0.05,
        1,
      );

    return [
      minimum,
      minimum + delta * 0.25,
      minimum + delta * 0.5,
      minimum + delta * 0.75,
      minimum + delta,
    ];
  }

  const range =
    maximum - minimum;

  return [
    minimum,
    minimum + range * 0.25,
    minimum + range * 0.5,
    minimum + range * 0.75,
    maximum,
  ];
}


export function camsRobustFieldStops(
  payload = {},
) {
  const values =
    camsFiniteFieldValues(
      payload,
    );

  if (values.length < 5) {
    return camsFieldStops(
      payload.statistics,
    );
  }

  const p05 =
    camsPercentile(
      values,
      0.05,
    );

  const p25 =
    camsPercentile(
      values,
      0.25,
    );

  const p50 =
    camsPercentile(
      values,
      0.50,
    );

  const p75 =
    camsPercentile(
      values,
      0.75,
    );

  const p95 =
    camsPercentile(
      values,
      0.95,
    );

  const stops = [
    p05,
    p25,
    p50,
    p75,
    p95,
  ];

  if (
    stops.every(
      Number.isFinite,
    )
    && p95 > p05
  ) {
    return stops;
  }

  return camsFieldStops(
    payload.statistics,
  );
}


export function camsFillColorExpression(
  payload = {},
) {
  const stops =
    camsRobustFieldStops(
      payload,
    );

  return [
    'interpolate',
    ['linear'],
    ['get', 'value'],
    stops[0], CAMS_FIELD_COLORS[0],
    stops[1], CAMS_FIELD_COLORS[1],
    stops[2], CAMS_FIELD_COLORS[2],
    stops[3], CAMS_FIELD_COLORS[3],
    stops[4], CAMS_FIELD_COLORS[4],
  ];
}


export function camsFieldViewModel(
  payload = {},
) {
  const statistics =
    payload.statistics ?? {};

  const units =
    payload.pollutant?.units
    || 'µg/m³';

  const numberOrNull = (value) => {
    const numeric = Number(value);

    return Number.isFinite(numeric)
      ? numeric
      : null;
  };

  const stops =
    camsRobustFieldStops(
      payload,
    );

  return {
    pollutant:
      payload.pollutant?.label
      || payload.pollutant?.id
      || '—',
    units,
    minimum:
      numberOrNull(
        statistics.min,
      ),
    mean:
      numberOrNull(
        statistics.mean,
      ),
    maximum:
      numberOrNull(
        statistics.max,
      ),
    validTime:
      payload.valid_time
      || null,
    runTime:
      payload.run_time
      || null,
    leadHour:
      numberOrNull(
        payload.lead_hour,
      ),
    model:
      payload.model
      || 'ensemble',
    legendMin:
      stops[0],
    legendMid:
      stops[2],
    legendMax:
      stops[4],
  };
}
