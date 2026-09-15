export function normalizeElapsedSeconds(value) {
  const number = Number(value);

  if (!Number.isFinite(number) || number <= 0) {
    return 0;
  }

  return Math.floor(number);
}


export function formatElapsedSeconds(value) {
  const total = normalizeElapsedSeconds(value);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;

  if (hours > 0) {
    return [
      hours,
      String(minutes).padStart(2, '0'),
      String(seconds).padStart(2, '0'),
    ].join(':');
  }

  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}


export function longTaskViewModel({
  startedAtMs,
  nowMs = Date.now(),
  revealAfterMs = 500,
  slowAfterSeconds = 120,
} = {}) {
  if (startedAtMs === null || startedAtMs === undefined) {
    return {
      active: false,
      visible: false,
      elapsedSeconds: 0,
      elapsedText: '0:00',
      slow: false,
    };
  }

  const start = Number(startedAtMs);
  const now = Number(nowMs);

  if (!Number.isFinite(start) || !Number.isFinite(now) || now < start) {
    return {
      active: false,
      visible: false,
      elapsedSeconds: 0,
      elapsedText: '0:00',
      slow: false,
    };
  }

  const elapsedMs = now - start;
  const elapsedSeconds = normalizeElapsedSeconds(elapsedMs / 1000);

  return {
    active: true,
    visible: elapsedMs >= Math.max(0, Number(revealAfterMs) || 0),
    elapsedSeconds,
    elapsedText: formatElapsedSeconds(elapsedSeconds),
    slow: elapsedSeconds >= Math.max(0, Number(slowAfterSeconds) || 0),
  };
}
