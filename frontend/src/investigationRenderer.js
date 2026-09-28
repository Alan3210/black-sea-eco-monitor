import { t } from './i18n.js';


function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}


function evidenceTypeLabel(
  type,
  currentLanguage,
) {
  const keys = {
    source_report:
      'investigation.type.sourceReport',

    satellite_observation:
      'investigation.type.satelliteObservation',
  };

  return t(
    currentLanguage,
    keys[type]
      || 'investigation.type.unknown',
  );
}


function formatConfidence(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return '—';
  }

  return `${Math.round(number * 100)}%`;
}


function renderEvidenceRecord(
  record,
  currentLanguage,
) {
  const dataset =
    record?.provenance?.dataset_id
    || null;

  const source =
    record?.source
    || t(
      currentLanguage,
      'investigation.unknownSource',
    );

  return `
    <article class="investigation-evidence-card">
      <div class="investigation-evidence-card__header">
        <span class="investigation-evidence-card__type">
          ${escapeHtml(
            evidenceTypeLabel(
              record?.type,
              currentLanguage,
            ),
          )}
        </span>

        <span class="investigation-evidence-card__confidence">
          ${escapeHtml(
            formatConfidence(
              record?.confidence,
            ),
          )}
        </span>
      </div>

      <div class="investigation-evidence-card__source">
        ${escapeHtml(source)}
      </div>

      ${
        record?.title
          ? `
            <div class="investigation-evidence-card__title">
              ${escapeHtml(record.title)}
            </div>
          `
          : ''
      }

      ${
        record?.timestamp
          ? `
            <div class="investigation-evidence-card__meta">
              ${escapeHtml(record.timestamp)}
            </div>
          `
          : ''
      }

      ${
        dataset
          ? `
            <div class="investigation-evidence-card__meta">
              ${escapeHtml(
                t(
                  currentLanguage,
                  'investigation.dataset',
                ),
              )}: ${escapeHtml(dataset)}
            </div>
          `
          : ''
      }
    </article>
  `;
}


export function renderInvestigationBlock(
  viewModel = {},
  currentLanguage = 'en',
) {
  const evidence = Array.isArray(
    viewModel.evidence,
  )
    ? viewModel.evidence
    : [];

  if (!evidence.length) {
    return `
      <div class="investigation-empty">
        ${escapeHtml(
          t(
            currentLanguage,
            'investigation.noEvidence',
          ),
        )}
      </div>
    `;
  }

  return `
    <div class="investigation-summary">
      <div class="investigation-summary__metric">
        <span>
          ${escapeHtml(
            t(
              currentLanguage,
              'investigation.evidenceCount',
            ),
          )}
        </span>

        <strong>
          ${escapeHtml(
            viewModel.evidenceCount
              ?? evidence.length,
          )}
        </strong>
      </div>

      <div class="investigation-summary__metric">
        <span>
          ${escapeHtml(
            t(
              currentLanguage,
              'investigation.candidateSources',
            ),
          )}
        </span>

        <strong>
          ${escapeHtml(
            viewModel.candidateSourceCount
              ?? 0,
          )}
        </strong>
      </div>
    </div>

    <div class="investigation-evidence-list">
      ${evidence
        .map((record) =>
          renderEvidenceRecord(
            record,
            currentLanguage,
          ),
        )
        .join('')}
    </div>
  `;
}