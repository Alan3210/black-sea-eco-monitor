const DEFAULT_WIND_PARTICLE_COUNT = 1200;
const MIN_WIND_PARTICLE_COUNT = 400;
const MAX_WIND_PARTICLE_COUNT = 2400;

const DEFAULT_WIND_PARTICLE_SPEED_PERCENT = 100;
const MIN_WIND_PARTICLE_SPEED_PERCENT = 50;
const MAX_WIND_PARTICLE_SPEED_PERCENT = 200;

const DEFAULT_WIND_PARTICLE_TRAIL_PERCENT = 55;
const MIN_WIND_PARTICLE_TRAIL_PERCENT = 10;
const MAX_WIND_PARTICLE_TRAIL_PERCENT = 100;

const DEFAULT_WIND_PARTICLE_SIZE_PERCENT = 120;
const MIN_WIND_PARTICLE_SIZE_PERCENT = 60;
const MAX_WIND_PARTICLE_SIZE_PERCENT = 200;

// A 10 m wind field is orders of magnitude faster than surface
// currents, so the visual acceleration must be much smaller than
// the current-particle engine's scale.
const WIND_VISUAL_TIME_SCALE_SECONDS = 3600;
const METERS_PER_DEGREE_LATITUDE = 111_320;


function finiteNumber(value) {
  if (
    value === null
    || value === undefined
    || value === ''
  ) {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : null;
}


function clampRounded(
  value,
  {
    min,
    max,
    step,
    fallback,
  },
) {
  const number = finiteNumber(value);

  if (number === null) {
    return fallback;
  }

  const clamped = Math.min(
    max,
    Math.max(min, number),
  );

  return Math.round(
    clamped / step,
  ) * step;
}


export function normalizeWindParticleCount(
  value,
  fallback = DEFAULT_WIND_PARTICLE_COUNT,
) {
  return clampRounded(
    value,
    {
      min: MIN_WIND_PARTICLE_COUNT,
      max: MAX_WIND_PARTICLE_COUNT,
      step: 100,
      fallback,
    },
  );
}


export function normalizeWindParticleSpeedPercent(
  value,
  fallback = DEFAULT_WIND_PARTICLE_SPEED_PERCENT,
) {
  return clampRounded(
    value,
    {
      min: MIN_WIND_PARTICLE_SPEED_PERCENT,
      max: MAX_WIND_PARTICLE_SPEED_PERCENT,
      step: 10,
      fallback,
    },
  );
}


export function normalizeWindParticleTrailPercent(
  value,
  fallback = DEFAULT_WIND_PARTICLE_TRAIL_PERCENT,
) {
  return clampRounded(
    value,
    {
      min: MIN_WIND_PARTICLE_TRAIL_PERCENT,
      max: MAX_WIND_PARTICLE_TRAIL_PERCENT,
      step: 10,
      fallback,
    },
  );
}


export function normalizeWindParticleSizePercent(
  value,
  fallback = DEFAULT_WIND_PARTICLE_SIZE_PERCENT,
) {
  return clampRounded(
    value,
    {
      min: MIN_WIND_PARTICLE_SIZE_PERCENT,
      max: MAX_WIND_PARTICLE_SIZE_PERCENT,
      step: 10,
      fallback,
    },
  );
}


export function normalizeWindDisplayMode(
  value,
  fallback = 'arrows',
) {
  return [
    'arrows',
    'particles',
    'both',
  ].includes(value)
    ? value
    : fallback;
}


function median(values) {
  if (!values.length) {
    return null;
  }

  const sorted = [
    ...values,
  ].sort(
    (a, b) => a - b,
  );

  const middle = Math.floor(
    sorted.length / 2,
  );

  if (sorted.length % 2) {
    return sorted[middle];
  }

  return (
    sorted[middle - 1]
    + sorted[middle]
  ) / 2;
}


function approximateGridStep(
  vectors,
) {
  const longitudes = [
    ...new Set(
      vectors.map(
        (vector) => vector.longitude,
      ),
    ),
  ].sort((a, b) => a - b);

  const latitudes = [
    ...new Set(
      vectors.map(
        (vector) => vector.latitude,
      ),
    ),
  ].sort((a, b) => a - b);

  const differences = [];

  for (const values of [
    longitudes,
    latitudes,
  ]) {
    for (
      let index = 1;
      index < values.length;
      index += 1
    ) {
      const difference =
        values[index]
        - values[index - 1];

      if (
        difference > 0.00001
        && difference < 2
      ) {
        differences.push(
          difference,
        );
      }
    }
  }

  const result = median(
    differences,
  );

  if (
    result === null
    || !Number.isFinite(result)
  ) {
    return 0.5;
  }

  return Math.max(
    0.05,
    Math.min(
      1,
      result,
    ),
  );
}


function fieldKey(
  longitude,
  latitude,
  field,
) {
  const x = Math.floor(
    (
      longitude
      - field.minLongitude
    )
    / field.cellSize,
  );

  const y = Math.floor(
    (
      latitude
      - field.minLatitude
    )
    / field.cellSize,
  );

  return `${x}:${y}`;
}


function coordinateKey(
  longitude,
  latitude,
) {
  return `${longitude}|${latitude}`;
}


function uniqueSorted(values) {
  return [
    ...new Set(values),
  ].sort(
    (a, b) => a - b,
  );
}


function bracketGridAxis(
  values,
  coordinate,
) {
  if (
    !Array.isArray(values)
    || values.length < 2
    || !Number.isFinite(coordinate)
  ) {
    return null;
  }

  const first =
    values[0];

  const last =
    values[
      values.length - 1
    ];

  const epsilon =
    Math.max(
      1e-9,
      Math.abs(
        last - first,
      ) * 1e-10,
    );

  if (
    coordinate
      < first - epsilon
    || coordinate
      > last + epsilon
  ) {
    return null;
  }

  if (
    coordinate <= first
  ) {
    return {
      lowerIndex: 0,
      upperIndex: 1,
      fraction: 0,
    };
  }

  if (
    coordinate >= last
  ) {
    return {
      lowerIndex:
        values.length - 2,
      upperIndex:
        values.length - 1,
      fraction: 1,
    };
  }

  let low = 0;
  let high =
    values.length - 1;

  while (
    high - low > 1
  ) {
    const middle =
      Math.floor(
        (
          low + high
        ) / 2,
      );

    if (
      values[middle]
      <= coordinate
    ) {
      low = middle;
    } else {
      high = middle;
    }
  }

  const lower =
    values[low];

  const upper =
    values[high];

  const span =
    upper - lower;

  if (
    span <= 0
  ) {
    return null;
  }

  return {
    lowerIndex: low,
    upperIndex: high,
    fraction:
      Math.max(
        0,
        Math.min(
          1,
          (
            coordinate
            - lower
          )
          / span,
        ),
      ),
  };
}


export function buildWindVectorField(
  vectors,
) {
  const usable = (
    Array.isArray(vectors)
      ? vectors
      : []
  )
    .map((vector) => {
      const longitude = finiteNumber(
        vector?.longitude,
      );
      const latitude = finiteNumber(
        vector?.latitude,
      );
      const u = finiteNumber(
        vector?.u,
      );
      const v = finiteNumber(
        vector?.v,
      );
      const speed = finiteNumber(
        vector?.speed,
      );

      if (
        longitude === null
        || latitude === null
        || u === null
        || v === null
        || speed === null
      ) {
        return null;
      }

      return {
        longitude,
        latitude,
        u,
        v,
        speed,
      };
    })
    .filter(Boolean);

  if (!usable.length) {
    return {
      vectors: [],
      buckets: new Map(),
      grid: new Map(),
      longitudeAxis: [],
      latitudeAxis: [],
      isRegularGrid: false,
      minLongitude: 0,
      maxLongitude: 0,
      minLatitude: 0,
      maxLatitude: 0,
      cellSize: 0.5,
      maxSampleDistance: 0.9,
    };
  }

  const longitudes = usable.map(
    (vector) => vector.longitude,
  );
  const latitudes = usable.map(
    (vector) => vector.latitude,
  );

  const longitudeAxis =
    uniqueSorted(
      longitudes,
    );

  const latitudeAxis =
    uniqueSorted(
      latitudes,
    );

  const field = {
    vectors: usable,
    buckets: new Map(),
    grid: new Map(),
    longitudeAxis,
    latitudeAxis,
    isRegularGrid: false,
    minLongitude: Math.min(
      ...longitudes,
    ),
    maxLongitude: Math.max(
      ...longitudes,
    ),
    minLatitude: Math.min(
      ...latitudes,
    ),
    maxLatitude: Math.max(
      ...latitudes,
    ),
    cellSize: approximateGridStep(
      usable,
    ),
    maxSampleDistance: 0,
  };

  field.maxSampleDistance =
    field.cellSize * 1.65;

  for (const vector of usable) {
    const key = fieldKey(
      vector.longitude,
      vector.latitude,
      field,
    );

    if (!field.buckets.has(key)) {
      field.buckets.set(
        key,
        [],
      );
    }

    field.buckets
      .get(key)
      .push(vector);

    field.grid.set(
      coordinateKey(
        vector.longitude,
        vector.latitude,
      ),
      vector,
    );
  }

  field.isRegularGrid =
    longitudeAxis.length >= 2
    && latitudeAxis.length >= 2
    && field.grid.size
      === (
        longitudeAxis.length
        * latitudeAxis.length
      );

  return field;
}


function normalizeMapBounds(
  bounds,
) {
  if (!bounds) {
    return null;
  }

  const read = (
    property,
    method,
  ) => {
    const direct = finiteNumber(
      bounds?.[property],
    );

    if (direct !== null) {
      return direct;
    }

    const fn =
      bounds?.[method];

    if (
      typeof fn
      !== 'function'
    ) {
      return null;
    }

    return finiteNumber(
      fn.call(bounds),
    );
  };

  const west = read(
    'west',
    'getWest',
  );
  const east = read(
    'east',
    'getEast',
  );
  const south = read(
    'south',
    'getSouth',
  );
  const north = read(
    'north',
    'getNorth',
  );

  if (
    west === null
    || east === null
    || south === null
    || north === null
    || east <= west
    || north <= south
  ) {
    return null;
  }

  return {
    west,
    east,
    south,
    north,
  };
}


export function windParticleSeedBounds(
  field,
  mapBounds,
  paddingRatio = 0.12,
) {
  if (
    !field?.vectors?.length
  ) {
    return null;
  }

  const bounds =
    normalizeMapBounds(
      mapBounds,
    );

  if (!bounds) {
    return {
      west:
        field.minLongitude,
      east:
        field.maxLongitude,
      south:
        field.minLatitude,
      north:
        field.maxLatitude,
    };
  }

  const padding =
    Math.max(
      0,
      Math.min(
        0.4,
        finiteNumber(
          paddingRatio,
        ) ?? 0.12,
      ),
    );

  const longitudePadding =
    (
      bounds.east
      - bounds.west
    )
    * padding;

  const latitudePadding =
    (
      bounds.north
      - bounds.south
    )
    * padding;

  const west =
    Math.max(
      field.minLongitude,
      bounds.west
      - longitudePadding,
    );

  const east =
    Math.min(
      field.maxLongitude,
      bounds.east
      + longitudePadding,
    );

  const south =
    Math.max(
      field.minLatitude,
      bounds.south
      - latitudePadding,
    );

  const north =
    Math.min(
      field.maxLatitude,
      bounds.north
      + latitudePadding,
    );

  if (
    east <= west
    || north <= south
  ) {
    return null;
  }

  return {
    west,
    east,
    south,
    north,
  };
}


function sampleWindVectorInverseDistance(
  field,
  longitude,
  latitude,
) {
  const centerX = Math.floor(
    (
      longitude
      - field.minLongitude
    )
    / field.cellSize,
  );

  const centerY = Math.floor(
    (
      latitude
      - field.minLatitude
    )
    / field.cellSize,
  );

  const candidates = [];

  for (
    let offsetX = -1;
    offsetX <= 1;
    offsetX += 1
  ) {
    for (
      let offsetY = -1;
      offsetY <= 1;
      offsetY += 1
    ) {
      const key =
        `${centerX + offsetX}:`
        + `${centerY + offsetY}`;

      const bucket =
        field.buckets.get(key)
        ?? [];

      for (
        const candidate
        of bucket
      ) {
        const dx =
          candidate.longitude
          - longitude;

        const dy =
          candidate.latitude
          - latitude;

        const distanceSquared =
          dx * dx
          + dy * dy;

        if (
          Math.sqrt(
            distanceSquared,
          )
          <= field.maxSampleDistance
        ) {
          candidates.push({
            candidate,
            distanceSquared,
          });
        }
      }
    }
  }

  if (!candidates.length) {
    return null;
  }

  candidates.sort(
    (a, b) =>
      a.distanceSquared
      - b.distanceSquared,
  );

  const nearest =
    candidates.slice(
      0,
      8,
    );

  if (
    nearest[0]
      .distanceSquared
      <= 1e-14
  ) {
    return nearest[0]
      .candidate;
  }

  let totalWeight = 0;
  let u = 0;
  let v = 0;

  for (
    const item
    of nearest
  ) {
    const weight =
      1
      / (
        item.distanceSquared
        + 1e-12
      );

    totalWeight +=
      weight;

    u +=
      item.candidate.u
      * weight;

    v +=
      item.candidate.v
      * weight;
  }

  if (
    totalWeight <= 0
  ) {
    return null;
  }

  u /= totalWeight;
  v /= totalWeight;

  return {
    longitude,
    latitude,
    u,
    v,
    speed:
      Math.hypot(
        u,
        v,
      ),
  };
}


function sampleRegularWindGrid(
  field,
  longitude,
  latitude,
) {
  const longitudeBracket =
    bracketGridAxis(
      field.longitudeAxis,
      longitude,
    );

  const latitudeBracket =
    bracketGridAxis(
      field.latitudeAxis,
      latitude,
    );

  if (
    !longitudeBracket
    || !latitudeBracket
  ) {
    return null;
  }

  const lon0 =
    field.longitudeAxis[
      longitudeBracket
        .lowerIndex
    ];

  const lon1 =
    field.longitudeAxis[
      longitudeBracket
        .upperIndex
    ];

  const lat0 =
    field.latitudeAxis[
      latitudeBracket
        .lowerIndex
    ];

  const lat1 =
    field.latitudeAxis[
      latitudeBracket
        .upperIndex
    ];

  const q00 =
    field.grid.get(
      coordinateKey(
        lon0,
        lat0,
      ),
    );

  const q10 =
    field.grid.get(
      coordinateKey(
        lon1,
        lat0,
      ),
    );

  const q01 =
    field.grid.get(
      coordinateKey(
        lon0,
        lat1,
      ),
    );

  const q11 =
    field.grid.get(
      coordinateKey(
        lon1,
        lat1,
      ),
    );

  if (
    !q00
    || !q10
    || !q01
    || !q11
  ) {
    return null;
  }

  const tx =
    longitudeBracket
      .fraction;

  const ty =
    latitudeBracket
      .fraction;

  const lowerU =
    q00.u
    + (
      q10.u
      - q00.u
    ) * tx;

  const upperU =
    q01.u
    + (
      q11.u
      - q01.u
    ) * tx;

  const lowerV =
    q00.v
    + (
      q10.v
      - q00.v
    ) * tx;

  const upperV =
    q01.v
    + (
      q11.v
      - q01.v
    ) * tx;

  const u =
    lowerU
    + (
      upperU
      - lowerU
    ) * ty;

  const v =
    lowerV
    + (
      upperV
      - lowerV
    ) * ty;

  return {
    longitude,
    latitude,
    u,
    v,
    speed:
      Math.hypot(
        u,
        v,
      ),
  };
}


export function sampleWindVector(
  field,
  longitude,
  latitude,
) {
  if (
    !field?.vectors?.length
    || !Number.isFinite(longitude)
    || !Number.isFinite(latitude)
  ) {
    return null;
  }

  if (
    longitude
      < field.minLongitude
        - field.maxSampleDistance
    || longitude
      > field.maxLongitude
        + field.maxSampleDistance
    || latitude
      < field.minLatitude
        - field.maxSampleDistance
    || latitude
      > field.maxLatitude
        + field.maxSampleDistance
  ) {
    return null;
  }

  // The ECMWF endpoint exposes a regular latitude/longitude grid.
  // Particle trajectories must not use nearest-neighbour sampling:
  // that makes u/v piecewise constant inside every grid cell and
  // exposes the grid as horizontal/vertical seams in accumulated
  // trails. Bilinear interpolation keeps u and v continuous across
  // cell boundaries.
  if (
    field.isRegularGrid
  ) {
    const interpolated =
      sampleRegularWindGrid(
        field,
        longitude,
        latitude,
      );

    if (interpolated) {
      return interpolated;
    }
  }

  // Defensive fallback for incomplete or degenerate fields. IDW is
  // still spatially smooth and avoids reintroducing the old hard
  // nearest-neighbour cell transitions.
  return sampleWindVectorInverseDistance(
    field,
    longitude,
    latitude,
  );
}


export function advectWindPosition(
  {
    longitude,
    latitude,
  },
  vector,
  elapsedSeconds,
  speedPercent =
    DEFAULT_WIND_PARTICLE_SPEED_PERCENT,
) {
  if (
    !vector
    || !Number.isFinite(longitude)
    || !Number.isFinite(latitude)
    || !Number.isFinite(elapsedSeconds)
  ) {
    return {
      longitude,
      latitude,
    };
  }

  const speedScale =
    normalizeWindParticleSpeedPercent(
      speedPercent,
    ) / 100;

  const simulatedSeconds =
    Math.max(
      0,
      elapsedSeconds,
    )
    * WIND_VISUAL_TIME_SCALE_SECONDS
    * speedScale;

  const latitudeRadians =
    latitude
    * Math.PI
    / 180;

  const metersPerDegreeLongitude =
    METERS_PER_DEGREE_LATITUDE
    * Math.max(
      0.1,
      Math.cos(
        latitudeRadians,
      ),
    );

  return {
    longitude:
      longitude
      + (
        vector.u
        * simulatedSeconds
        / metersPerDegreeLongitude
      ),
    latitude:
      latitude
      + (
        vector.v
        * simulatedSeconds
        / METERS_PER_DEGREE_LATITUDE
      ),
  };
}


export function windTrailRetention(
  trailPercent =
    DEFAULT_WIND_PARTICLE_TRAIL_PERCENT,
) {
  const normalized =
    normalizeWindParticleTrailPercent(
      trailPercent,
    );

  const ratio =
    (
      normalized
      - MIN_WIND_PARTICLE_TRAIL_PERCENT
    )
    / (
      MAX_WIND_PARTICLE_TRAIL_PERCENT
      - MIN_WIND_PARTICLE_TRAIL_PERCENT
    );

  return (
    0.62
    + ratio * 0.365
  );
}


export function windParticleStrokeStyle(
  speed,
  sizePercent =
    DEFAULT_WIND_PARTICLE_SIZE_PERCENT,
) {
  const numericSpeed =
    Math.max(
      0,
      Math.min(
        18,
        finiteNumber(speed) ?? 0,
      ),
    );

  const ratio =
    numericSpeed / 18;

  const sizeScale =
    normalizeWindParticleSizePercent(
      sizePercent,
    ) / 100;

  // The previous cyan stroke was physically correct but visually
  // too close to the pale OSM water fill. Use a bright ice-cyan core
  // with a dark navy halo so the flow remains readable over water,
  // land, roads and other MapLibre layers.
  const lightness =
    86
    + 8 * ratio;

  const alpha =
    0.90
    + 0.08 * ratio;

  const coreWidth =
    (
      1.05
      + 1.65 * ratio
    )
    * sizeScale;

  return {
    color:
      `hsla(184, 100%, ${lightness}%, ${alpha})`,
    width:
      coreWidth,
    haloColor:
      'rgba(4, 18, 30, 0.82)',
    haloWidth:
      coreWidth
      + 2.2 * sizeScale,
  };
}


function randomFromArray(
  values,
) {
  if (!values.length) {
    return null;
  }

  return values[
    Math.floor(
      Math.random()
      * values.length,
    )
  ];
}


export class WindParticleEngine {
  constructor({
    canvas,
    map,
    particleCount =
      DEFAULT_WIND_PARTICLE_COUNT,
    speedPercent =
      DEFAULT_WIND_PARTICLE_SPEED_PERCENT,
    trailPercent =
      DEFAULT_WIND_PARTICLE_TRAIL_PERCENT,
    sizePercent =
      DEFAULT_WIND_PARTICLE_SIZE_PERCENT,
  }) {
    if (!canvas) {
      throw new Error(
        'Wind particle canvas is required.',
      );
    }

    if (!map) {
      throw new Error(
        'MapLibre map instance is required.',
      );
    }

    this.canvas = canvas;
    this.map = map;
    this.context =
      canvas.getContext('2d');

    if (!this.context) {
      throw new Error(
        'Canvas 2D context is unavailable.',
      );
    }

    this.field =
      buildWindVectorField([]);

    this.particles = [];
    this.particleCount =
      normalizeWindParticleCount(
        particleCount,
      );

    this.speedPercent =
      normalizeWindParticleSpeedPercent(
        speedPercent,
      );

    this.trailPercent =
      normalizeWindParticleTrailPercent(
        trailPercent,
      );

    this.sizePercent =
      normalizeWindParticleSizePercent(
        sizePercent,
      );

    this.running = false;
    this.animationFrame = null;
    this.lastTimestamp = null;

    this.resize();
    this.reseed();
  }

  setField(payload) {
    const vectors =
      Array.isArray(payload)
        ? payload
        : payload?.vectors;

    this.field =
      buildWindVectorField(
        vectors,
      );

    this.reseed();
    this.clear();
  }

  setParticleCount(value) {
    this.particleCount =
      normalizeWindParticleCount(
        value,
      );

    this.reseed();
  }

  setSpeedPercent(value) {
    this.speedPercent =
      normalizeWindParticleSpeedPercent(
        value,
      );
  }

  setTrailPercent(value) {
    this.trailPercent =
      normalizeWindParticleTrailPercent(
        value,
      );
  }

  setSizePercent(value) {
    this.sizePercent =
      normalizeWindParticleSizePercent(
        value,
      );
  }

  resize() {
    const mapCanvas =
      this.map.getCanvas();

    const rect =
      mapCanvas
        .getBoundingClientRect();

    const ratio = Math.min(
      2,
      window.devicePixelRatio
      || 1,
    );

    this.canvas.width =
      Math.max(
        1,
        Math.round(
          rect.width * ratio,
        ),
      );

    this.canvas.height =
      Math.max(
        1,
        Math.round(
          rect.height * ratio,
        ),
      );

    this.canvas.style.width =
      `${rect.width}px`;

    this.canvas.style.height =
      `${rect.height}px`;

    this.context.setTransform(
      ratio,
      0,
      0,
      ratio,
      0,
      0,
    );

    this.clear();

    // moveend already calls resize(). Reseeding here makes the
    // particle population follow the currently visible viewport
    // instead of remaining distributed across the whole Black Sea.
    if (
      this.field?.vectors?.length
    ) {
      this.reseed();
    }
  }

  clear() {
    this.context.clearRect(
      0,
      0,
      this.canvas.clientWidth,
      this.canvas.clientHeight,
    );
  }

  reseed() {
    this.particles =
      Array.from(
        {
          length:
            this.particleCount,
        },
        () =>
          this.createParticle(
            true,
          ),
      );
  }

  createParticle(
    randomAge = false,
  ) {
    const mapBounds =
      typeof this.map.getBounds
      === 'function'
        ? this.map.getBounds()
        : null;

    const seedBounds =
      windParticleSeedBounds(
        this.field,
        mapBounds,
      );

    if (seedBounds) {
      // Prefer a uniformly distributed seed inside the visible
      // viewport. This is the key difference from v0.1, where all
      // particles were spread across the entire Black Sea and only
      // a handful were visible at regional zoom levels.
      for (
        let attempt = 0;
        attempt < 12;
        attempt += 1
      ) {
        const longitude =
          seedBounds.west
          + Math.random()
          * (
            seedBounds.east
            - seedBounds.west
          );

        const latitude =
          seedBounds.south
          + Math.random()
          * (
            seedBounds.north
            - seedBounds.south
          );

        if (
          sampleWindVector(
            this.field,
            longitude,
            latitude,
          )
        ) {
          return {
            longitude,
            latitude,
            age:
              randomAge
                ? Math.random() * 100
                : 0,
            life:
              70
              + Math.random() * 150,
          };
        }
      }
    }

    const vector =
      randomFromArray(
        this.field.vectors,
      );

    if (!vector) {
      return {
        longitude: null,
        latitude: null,
        age: 0,
        life: 70,
      };
    }

    const jitter =
      this.field.cellSize
      * 0.38;

    return {
      longitude:
        vector.longitude
        + (
          Math.random() - 0.5
        ) * jitter,
      latitude:
        vector.latitude
        + (
          Math.random() - 0.5
        ) * jitter,
      age:
        randomAge
          ? Math.random() * 100
          : 0,
      life:
        70
        + Math.random() * 150,
    };
  }

  resetParticle(
    particle,
    randomAge = false,
  ) {
    Object.assign(
      particle,
      this.createParticle(
        randomAge,
      ),
    );
  }

  fadeTrails() {
    const retention =
      windTrailRetention(
        this.trailPercent,
      );

    const context =
      this.context;

    context.save();
    context
      .globalCompositeOperation =
        'destination-in';

    context.fillStyle =
      `rgba(0, 0, 0, ${retention})`;

    context.fillRect(
      0,
      0,
      this.canvas.clientWidth,
      this.canvas.clientHeight,
    );

    context.restore();
  }

  drawParticle(
    particle,
    vector,
    nextPosition,
  ) {
    if (
      particle.longitude === null
      || particle.latitude === null
    ) {
      return;
    }

    const start =
      this.map.project([
        particle.longitude,
        particle.latitude,
      ]);

    const end =
      this.map.project([
        nextPosition.longitude,
        nextPosition.latitude,
      ]);

    if (
      !Number.isFinite(start.x)
      || !Number.isFinite(start.y)
      || !Number.isFinite(end.x)
      || !Number.isFinite(end.y)
    ) {
      return;
    }

    const margin = 80;
    const width =
      this.canvas.clientWidth;
    const height =
      this.canvas.clientHeight;

    if (
      (
        start.x < -margin
        && end.x < -margin
      )
      || (
        start.x > width + margin
        && end.x > width + margin
      )
      || (
        start.y < -margin
        && end.y < -margin
      )
      || (
        start.y > height + margin
        && end.y > height + margin
      )
    ) {
      return;
    }

    const style =
      windParticleStrokeStyle(
        vector.speed,
        this.sizePercent,
      );

    const context =
      this.context;

    context.beginPath();
    context.moveTo(
      start.x,
      start.y,
    );
    context.lineTo(
      end.x,
      end.y,
    );

    // First draw a dark halo. It is intentionally not a glow:
    // the halo provides deterministic contrast against both the
    // pale-blue sea and bright/green land tiles.
    context.strokeStyle =
      style.haloColor;

    context.lineWidth =
      style.haloWidth;

    context.lineCap =
      'round';

    context.stroke();

    // Then draw the bright wind core.
    context.strokeStyle =
      style.color;

    context.lineWidth =
      style.width;

    context.stroke();
  }

  tick(
    elapsedSeconds,
  ) {
    if (
      !this.field.vectors.length
    ) {
      this.clear();
      return;
    }

    this.fadeTrails();

    for (
      const particle
      of this.particles
    ) {
      if (
        particle.longitude === null
        || particle.latitude === null
      ) {
        this.resetParticle(
          particle,
        );
        continue;
      }

      const vector =
        sampleWindVector(
          this.field,
          particle.longitude,
          particle.latitude,
        );

      if (!vector) {
        this.resetParticle(
          particle,
        );
        continue;
      }

      const nextPosition =
        advectWindPosition(
          particle,
          vector,
          elapsedSeconds,
          this.speedPercent,
        );

      const nextVector =
        sampleWindVector(
          this.field,
          nextPosition.longitude,
          nextPosition.latitude,
        );

      if (!nextVector) {
        this.resetParticle(
          particle,
        );
        continue;
      }

      this.drawParticle(
        particle,
        vector,
        nextPosition,
      );

      particle.longitude =
        nextPosition.longitude;

      particle.latitude =
        nextPosition.latitude;

      particle.age += 1;

      if (
        particle.age
        >= particle.life
      ) {
        this.resetParticle(
          particle,
        );
      }
    }
  }

  frame(
    timestamp,
  ) {
    if (!this.running) {
      return;
    }

    if (
      this.lastTimestamp === null
    ) {
      this.lastTimestamp =
        timestamp;
    }

    const elapsedSeconds =
      Math.min(
        0.05,
        Math.max(
          0.001,
          (
            timestamp
            - this.lastTimestamp
          ) / 1000,
        ),
      );

    this.lastTimestamp =
      timestamp;

    this.tick(
      elapsedSeconds,
    );

    this.animationFrame =
      window.requestAnimationFrame(
        (nextTimestamp) => {
          this.frame(
            nextTimestamp,
          );
        },
      );
  }

  start() {
    if (this.running) {
      return;
    }

    this.running = true;
    this.lastTimestamp = null;

    this.animationFrame =
      window.requestAnimationFrame(
        (timestamp) => {
          this.frame(
            timestamp,
          );
        },
      );
  }

  stop({
    clear = true,
  } = {}) {
    this.running = false;
    this.lastTimestamp = null;

    if (
      this.animationFrame !== null
    ) {
      window.cancelAnimationFrame(
        this.animationFrame,
      );

      this.animationFrame = null;
    }

    if (clear) {
      this.clear();
    }
  }
}
