const VALID_DISPLAY_MODES =
  new Set([
    'arrows',
    'particles',
    'both',
  ]);


function finiteDateMs(value) {
  if (!value) {
    return null;
  }

  const milliseconds =
    Date.parse(value);

  return Number.isFinite(
    milliseconds,
  )
    ? milliseconds
    : null;
}


export function normalizeCombinedDisplayMode(
  value,
  fallback = 'arrows',
) {
  return VALID_DISPLAY_MODES.has(
    value,
  )
    ? value
    : fallback;
}



function finiteNonNegativeNumber(value) {
  if (
    value === null
    || value === undefined
    || value === ''
  ) {
    return null;
  }

  const number =
    Number(value);

  return (
    Number.isFinite(number)
    && number >= 0
  )
    ? number
    : null;
}


export function combinedWindMeanSpeedMs(
  windPayload,
) {
  const statMean =
    finiteNonNegativeNumber(
      windPayload
        ?.speed_stats
        ?.mean_speed_ms,
    );

  if (statMean !== null) {
    return statMean;
  }

  const speeds =
    (
      Array.isArray(
        windPayload?.vectors,
      )
        ? windPayload.vectors
        : []
    )
      .map(
        (vector) =>
          finiteNonNegativeNumber(
            vector?.speed,
          ),
      )
      .filter(
        (value) =>
          value !== null,
      );

  if (!speeds.length) {
    return null;
  }

  return (
    speeds.reduce(
      (sum, value) =>
        sum + value,
      0,
    )
    / speeds.length
  );
}


export function combinedFieldTimeDeltaMinutes(
  currentValidTime,
  windValidTime,
) {
  const currentMs =
    finiteDateMs(
      currentValidTime,
    );

  const windMs =
    finiteDateMs(
      windValidTime,
    );

  if (
    currentMs == null
    || windMs == null
  ) {
    return null;
  }

  return Math.round(
    Math.abs(
      currentMs
      - windMs,
    ) / 60000,
  );
}


export function combinedFieldsViewModel({
  currentsEnabled,
  windEnabled,
  currentsPayload,
  windPayload,
  currentsLoading = false,
  windLoading = false,
  currentsError = '',
  windError = '',
  currentDisplayMode = 'arrows',
  windDisplayMode = 'arrows',
} = {}) {
  const visible =
    Boolean(
      currentsEnabled
      && windEnabled,
    );

  if (!visible) {
    return {
      visible: false,
      state: 'hidden',
      timeDeltaMinutes: null,
      currentDisplayMode:
        normalizeCombinedDisplayMode(
          currentDisplayMode,
        ),
      windDisplayMode:
        normalizeCombinedDisplayMode(
          windDisplayMode,
        ),
    };
  }

  let state = 'ready';

  if (
    currentsError
    || windError
  ) {
    state = 'error';
  } else if (
    currentsLoading
    || windLoading
    || !currentsPayload
    || !windPayload
  ) {
    state = 'loading';
  }

  return {
    visible: true,
    state,
    timeDeltaMinutes:
      combinedFieldTimeDeltaMinutes(
        currentsPayload?.valid_time,
        windPayload?.valid_time,
      ),
    currentDisplayMode:
      normalizeCombinedDisplayMode(
        currentDisplayMode,
      ),
    windDisplayMode:
      normalizeCombinedDisplayMode(
        windDisplayMode,
      ),
    currentValidTime:
      currentsPayload?.valid_time
      ?? null,
    windValidTime:
      windPayload?.valid_time
      ?? null,
    windMeanSpeedMs:
      combinedWindMeanSpeedMs(
        windPayload,
      ),
    currentSource:
      currentsPayload?.source
      || 'Copernicus Marine',
    windSource:
      'ECMWF IFS',
  };
}
