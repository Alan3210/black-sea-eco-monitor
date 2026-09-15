const DEFAULT_PARTICLE_COUNT = 1800;
const MIN_PARTICLE_COUNT = 600;
const MAX_PARTICLE_COUNT = 3000;

const DEFAULT_SPEED_PERCENT = 100;
const MIN_SPEED_PERCENT = 50;
const MAX_SPEED_PERCENT = 200;

const DEFAULT_TRAIL_PERCENT = 70;
const MIN_TRAIL_PERCENT = 10;
const MAX_TRAIL_PERCENT = 100;

const VISUAL_TIME_SCALE_SECONDS = 180_000;
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

  return Math.round(clamped / step) * step;
}


export function normalizeParticleCount(
  value,
  fallback = DEFAULT_PARTICLE_COUNT,
) {
  return clampRounded(
    value,
    {
      min: MIN_PARTICLE_COUNT,
      max: MAX_PARTICLE_COUNT,
      step: 100,
      fallback,
    },
  );
}


export function normalizeParticleSpeedPercent(
  value,
  fallback = DEFAULT_SPEED_PERCENT,
) {
  return clampRounded(
    value,
    {
      min: MIN_SPEED_PERCENT,
      max: MAX_SPEED_PERCENT,
      step: 10,
      fallback,
    },
  );
}


export function normalizeParticleTrailPercent(
  value,
  fallback = DEFAULT_TRAIL_PERCENT,
) {
  return clampRounded(
    value,
    {
      min: MIN_TRAIL_PERCENT,
      max: MAX_TRAIL_PERCENT,
      step: 10,
      fallback,
    },
  );
}


export function normalizeCurrentDisplayMode(
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

  const sorted = [...values].sort(
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


function approximateGridStep(vectors) {
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
        && difference < 1
      ) {
        differences.push(difference);
      }
    }
  }

  const result = median(differences);

  if (
    result === null
    || !Number.isFinite(result)
  ) {
    return 0.25;
  }

  return Math.max(
    0.01,
    Math.min(0.5, result),
  );
}


function fieldKey(
  longitude,
  latitude,
  field,
) {
  const x = Math.floor(
    (longitude - field.minLongitude)
    / field.cellSize,
  );

  const y = Math.floor(
    (latitude - field.minLatitude)
    / field.cellSize,
  );

  return `${x}:${y}`;
}


export function buildCurrentVectorField(
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
      const u = finiteNumber(vector?.u);
      const v = finiteNumber(vector?.v);
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
      minLongitude: 0,
      maxLongitude: 0,
      minLatitude: 0,
      maxLatitude: 0,
      cellSize: 0.25,
      maxSampleDistance: 0.45,
    };
  }

  const longitudes = usable.map(
    (vector) => vector.longitude,
  );
  const latitudes = usable.map(
    (vector) => vector.latitude,
  );

  const field = {
    vectors: usable,
    buckets: new Map(),
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
      field.buckets.set(key, []);
    }

    field.buckets.get(key).push(
      vector,
    );
  }

  return field;
}


export function sampleCurrentVector(
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

  const centerX = Math.floor(
    (longitude - field.minLongitude)
    / field.cellSize,
  );

  const centerY = Math.floor(
    (latitude - field.minLatitude)
    / field.cellSize,
  );

  let best = null;
  let bestDistanceSquared = Infinity;

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

      const candidates =
        field.buckets.get(key)
        ?? [];

      for (const candidate of candidates) {
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
          distanceSquared
          < bestDistanceSquared
        ) {
          best = candidate;
          bestDistanceSquared =
            distanceSquared;
        }
      }
    }
  }

  if (!best) {
    return null;
  }

  if (
    Math.sqrt(bestDistanceSquared)
    > field.maxSampleDistance
  ) {
    return null;
  }

  return best;
}


export function advectPosition(
  {
    longitude,
    latitude,
  },
  vector,
  elapsedSeconds,
  speedPercent = DEFAULT_SPEED_PERCENT,
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
    normalizeParticleSpeedPercent(
      speedPercent,
    ) / 100;

  const simulatedSeconds =
    Math.max(0, elapsedSeconds)
    * VISUAL_TIME_SCALE_SECONDS
    * speedScale;

  const latitudeRadians =
    latitude
    * Math.PI
    / 180;

  const metersPerDegreeLongitude =
    METERS_PER_DEGREE_LATITUDE
    * Math.max(
      0.1,
      Math.cos(latitudeRadians),
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


export function trailRetention(
  trailPercent = DEFAULT_TRAIL_PERCENT,
) {
  const normalized =
    normalizeParticleTrailPercent(
      trailPercent,
    );

  const ratio =
    (
      normalized
      - MIN_TRAIL_PERCENT
    )
    / (
      MAX_TRAIL_PERCENT
      - MIN_TRAIL_PERCENT
    );

  return (
    0.68
    + ratio * 0.315
  );
}


export function particleStrokeStyle(
  speed,
) {
  const numericSpeed =
    Math.max(
      0,
      Math.min(
        0.7,
        finiteNumber(speed) ?? 0,
      ),
    );

  const ratio =
    numericSpeed / 0.7;

  const hue =
    50
    - 32 * ratio;

  const alpha =
    0.62
    + 0.30 * ratio;

  return {
    color:
      `hsla(${hue}, 100%, 55%, ${alpha})`,
    width:
      1.0
      + 1.8 * ratio,
  };
}


function randomFromArray(values) {
  if (!values.length) {
    return null;
  }

  return values[
    Math.floor(
      Math.random() * values.length,
    )
  ];
}


export class CurrentParticleEngine {
  constructor({
    canvas,
    map,
    particleCount = DEFAULT_PARTICLE_COUNT,
    speedPercent = DEFAULT_SPEED_PERCENT,
    trailPercent = DEFAULT_TRAIL_PERCENT,
  }) {
    if (!canvas) {
      throw new Error(
        'Particle canvas is required.',
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
      buildCurrentVectorField([]);

    this.particles = [];
    this.particleCount =
      normalizeParticleCount(
        particleCount,
      );

    this.speedPercent =
      normalizeParticleSpeedPercent(
        speedPercent,
      );

    this.trailPercent =
      normalizeParticleTrailPercent(
        trailPercent,
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
      buildCurrentVectorField(
        vectors,
      );

    this.reseed();
    this.clear();
  }

  setParticleCount(value) {
    this.particleCount =
      normalizeParticleCount(value);

    this.reseed();
  }

  setSpeedPercent(value) {
    this.speedPercent =
      normalizeParticleSpeedPercent(
        value,
      );
  }

  setTrailPercent(value) {
    this.trailPercent =
      normalizeParticleTrailPercent(
        value,
      );
  }

  resize() {
    const mapCanvas =
      this.map.getCanvas();

    const rect =
      mapCanvas.getBoundingClientRect();

    const ratio = Math.min(
      2,
      window.devicePixelRatio || 1,
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
        () => this.createParticle(true),
      );
  }

  createParticle(randomAge = false) {
    const vector =
      randomFromArray(
        this.field.vectors,
      );

    if (!vector) {
      return {
        longitude: null,
        latitude: null,
        age: 0,
        life: 60,
      };
    }

    const jitter =
      this.field.cellSize
      * 0.35;

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
      age: randomAge
        ? Math.random() * 120
        : 0,
      life:
        80
        + Math.random() * 180,
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
      trailRetention(
        this.trailPercent,
      );

    const ctx = this.context;

    ctx.save();
    ctx.globalCompositeOperation =
      'destination-in';

    ctx.fillStyle =
      `rgba(0, 0, 0, ${retention})`;

    ctx.fillRect(
      0,
      0,
      this.canvas.clientWidth,
      this.canvas.clientHeight,
    );

    ctx.restore();
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
      particleStrokeStyle(
        vector.speed,
      );

    const ctx = this.context;

    ctx.beginPath();
    ctx.moveTo(
      start.x,
      start.y,
    );
    ctx.lineTo(
      end.x,
      end.y,
    );

    ctx.strokeStyle =
      style.color;

    ctx.lineWidth =
      style.width;

    ctx.lineCap = 'round';
    ctx.stroke();
  }

  tick(elapsedSeconds) {
    if (!this.field.vectors.length) {
      this.clear();
      return;
    }

    this.fadeTrails();

    for (const particle of this.particles) {
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
        sampleCurrentVector(
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
        advectPosition(
          particle,
          vector,
          elapsedSeconds,
          this.speedPercent,
        );

      const nextVector =
        sampleCurrentVector(
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

  frame(timestamp) {
    if (!this.running) {
      return;
    }

    if (this.lastTimestamp === null) {
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
