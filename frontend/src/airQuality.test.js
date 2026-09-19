import test from "node:test";
import assert from "node:assert/strict";

import {
  airQualityColor,
  airStationToFeature,
  normalizeAirStatus,
  airStationsToGeoJSON,
} from "./airQuality.js";


test("normalizes generic air status", () => {
  assert.equal(
    normalizeAirStatus("good"),
    "good"
  );

  assert.equal(
    normalizeAirStatus("bad-value"),
    "unknown"
  );
});


test("creates provider-neutral station feature", () => {
  const feature =
    airStationToFeature({
      id: "station-1",
      name: "Test",
      lat: 44.7,
      lon: 37.7,
      status: "good",
      pm25: 10,
      source: "EEA",
      observed_at:
        "2026-09-19T10:00:00Z",
    });

  assert.deepEqual(
    feature.geometry.coordinates,
    [37.7, 44.7]
  );

  assert.equal(
    feature.properties.source,
    "EEA"
  );

  assert.equal(
    feature.properties.observed_at,
    "2026-09-19T10:00:00Z"
  );
});


test("creates feature collection", () => {
  const collection =
    airStationsToGeoJSON([
      {
        id: "1",
        lat: 1,
        lon: 2,
        status: "moderate",
      },
    ]);

  assert.equal(
    collection.features.length,
    1
  );
});


test("uses provider-neutral fallback source", () => {
  const feature =
    airStationToFeature({
      id: "1",
      lat: 1,
      lon: 2,
    });

  assert.equal(
    feature.properties.source,
    "Ground observation"
  );
});


test("returns readable colors", () => {
  assert.equal(
    airQualityColor("poor"),
    "#ff6b6b"
  );
});
