import {
  fetchInvestigation,
} from './investigationApi.js';

import {
  normalizeInvestigationPayload,
} from './investigationNormalizer.js';

import {
  buildInvestigationViewModel,
} from './investigationViewModel.js';


export async function loadInvestigationViewModel(
  href,
  fetchImpl = fetch,
) {
  if (!href) {
    return buildInvestigationViewModel();
  }

  const payload =
    await fetchInvestigation(
      href,
      fetchImpl,
    );

  const normalized =
    normalizeInvestigationPayload(
      payload,
    );

  return buildInvestigationViewModel(
    normalized,
  );
}