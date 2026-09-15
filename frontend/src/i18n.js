export const DEFAULT_LANGUAGE = 'ru';
export const SUPPORTED_LANGUAGES = Object.freeze(['ru', 'en']);

const LOCALES = Object.freeze({
  ru: 'ru-RU',
  en: 'en-US',
});

const TRANSLATIONS = {
  ru: {
    'site.title': 'Экомонитор Чёрного моря',
    'site.eyebrow': 'ЭКОЛОГИЧЕСКАЯ АНАЛИТИКА',
    'site.description': 'Карта экологических происшествий в Черноморском регионе',

    'language.label': 'Язык интерфейса',
    'language.ru': 'Русский',
    'language.en': 'English',

    'connection.connecting': 'Подключение…',
    'connection.waiting': 'Ожидание API',
    'connection.online': 'Мониторинг активен',
    'connection.updated': 'Обновлено {time}',
    'connection.offline': 'Мониторинг офлайн',
    'connection.lastKnown': 'Показаны последние данные · Обновлено {time}',
    'connection.unavailable': 'Мониторинг недоступен',

    'filters.aria': 'Фильтры событий',
    'filters.kicker': 'ФИЛЬТРЫ',
    'filters.title': 'События',
    'filters.reset': 'Сбросить',
    'filters.status': 'СТАТУС',
    'filters.category': 'КАТЕГОРИЯ',
    'filters.moreCategories': 'Другие категории',
    'filters.timeWindow': 'ПЕРИОД',
    'filters.timeWindowAria': 'Период времени',
    'filters.24h': '24 Ч',
    'filters.7d': '7 Д',
    'filters.30d': '30 Д',
    'filters.all': 'ВСЁ',
    'filters.timeNote': 'Период определяется по времени инцидента, затем публикации и обнаружения.',

    'status.detected': 'Обнаружено',
    'status.active': 'Активно',
    'status.contained': 'Локализовано',
    'status.resolved': 'Завершено',
    'status.unknown': 'Неизвестно',

    'severity.low': 'Низкая',
    'severity.medium': 'Средняя',
    'severity.high': 'Высокая',
    'severity.unknown': 'Неизвестно',

    'category.wildfire': 'Лесной пожар',
    'category.industrial_fire': 'Промышленный пожар',
    'category.oil_spill': 'Разлив нефти',
    'category.water_pollution': 'Загрязнение воды',
    'category.algae_bloom': 'Цветение водорослей',
    'category.marine_animal_death': 'Гибель морских животных',
    'category.chemical_release': 'Химический выброс',
    'category.storm_damage': 'Штормовой ущерб',
    'category.unknown': 'Экологическое происшествие',

    'legend.aria': 'Легенда событий',
    'legend.title': 'СОБЫТИЯ',

    'map.aria': 'Карта экологических происшествий Черноморского региона',
    'map.zoomIn': 'Приблизить',
    'map.zoomOut': 'Отдалить',
    'map.resetBearing': 'Сбросить направление карты',
    'map.attribution': 'Информация об источниках карты',
    'map.incidentsShort': 'СОБЫТИЯ',
    'map.groupAria': '{count} событий в точке {location}',

    'panel.aria': 'Информация о выбранном событии',
    'panel.close': 'Закрыть информацию о событии',
    'panel.eventConfidence': 'УВЕРЕННОСТЬ В СОБЫТИИ',
    'panel.locationConfidence': 'УВЕРЕННОСТЬ В ЛОКАЦИИ',
    'panel.evidence': 'ИСТОЧНИКИ',
    'panel.coordinates': 'КООРДИНАТЫ',
    'panel.locationQuality': 'КАЧЕСТВО ЛОКАЦИИ',
    'panel.locationType': 'ТИП ЛОКАЦИИ',
    'panel.mapScope': 'МАСШТАБ ТОЧНОСТИ',
    'panel.coordinateSource': 'ИСТОЧНИК КООРДИНАТ',
    'panel.timeline': 'ВРЕМЕННАЯ ШКАЛА',
    'panel.incidentTime': 'ВРЕМЯ ИНЦИДЕНТА',
    'panel.sourceTime': 'ВРЕМЯ ПУБЛИКАЦИИ',
    'panel.detected': 'ОБНАРУЖЕНО СИСТЕМОЙ',
    'panel.firstSeen': 'ПЕРВОЕ НАБЛЮДЕНИЕ',
    'panel.latest': 'ПОСЛЕДНЕЕ ОБНОВЛЕНИЕ',
    'panel.evidenceHeading': 'ИСТОЧНИКИ · {count}',
    'panel.loadingSources': 'Загрузка источников…',
    'panel.noEvidence': 'Нет записей источников.',
    'panel.untitledSource': 'Источник без заголовка',
    'panel.unknownSource': 'Неизвестный источник',
    'panel.openSource': 'Открыть источник ↗',
    'panel.evidenceUnavailable': 'Источники недоступны: {message}',

    'group.kicker': 'СОБЫТИЯ В ОДНОЙ ТОЧКЕ',
    'group.summary': '{count} используют одну каноническую точку на карте. Выберите событие, чтобы посмотреть источники и жизненный цикл.',
    'group.back': '← {count} в этой точке',
    'group.cardMeta': 'Важность: {severity} · Уверенность: {confidence} · Источники: {evidence}',

    'location.unknown': 'Неизвестная локация',
    'headline.fallback': 'Экологическое происшествие',

    'locationType.city': 'Город',
    'locationType.settlement': 'Населённый пункт',
    'locationType.district': 'Район',
    'locationType.street': 'Улица',
    'locationType.facility': 'Объект',
    'locationType.protected_area': 'Охраняемая территория',
    'locationType.coastal_area': 'Прибрежная зона',
    'locationType.water_body': 'Водный объект',
    'locationType.region': 'Регион',
    'locationType.other': 'Другое',
    'locationType.unknown': 'Неизвестно',

    'locationScope.city': 'Уровень города',
    'locationScope.settlement': 'Уровень населённого пункта',
    'locationScope.district': 'Уровень района',
    'locationScope.street': 'Уровень улицы',
    'locationScope.facility': 'Уровень объекта',
    'locationScope.protected_area': 'Охраняемая территория',
    'locationScope.coastal_area': 'Прибрежная зона',
    'locationScope.water_body': 'Водный объект',
    'locationScope.region': 'Уровень региона',
    'locationScope.other': 'Приблизительно',
    'locationScope.unknown': 'Неизвестно',

    'coordinateSource.canonical_database': 'Каноническая база координат',
    'coordinateSource.geocoded_address': 'Геокодированный адрес',
    'coordinateSource.llm_extraction': 'Извлечено моделью',
    'coordinateSource.manual_review': 'Ручная проверка',
    'coordinateSource.satellite_detection': 'Спутниковое обнаружение',
    'coordinateSource.unknown': 'Неизвестно',

    'coordinateNote.canonical': 'Условная точка локации — не точные координаты инцидента.',
    'coordinateNote.provenance': 'У координат указан источник; точность необходимо проверять перед полевым использованием.',
    'coordinateNote.unknown': 'Источник координат недоступен.',

    'eventCount.one': '{count} событие',
    'eventCount.few': '{count} события',
    'eventCount.many': '{count} событий',
    'eventCount.filtered': '{visible} из {total} событий',

    'canonicalLocation.Novorossiysk': 'Новороссийск',
    'canonicalLocation.Gelendzhik': 'Геленджик',
    'canonicalLocation.Anapa': 'Анапа',
    'canonicalLocation.Sochi': 'Сочи',
    'canonicalLocation.Sevastopol': 'Севастополь',
    'canonicalLocation.Utrish Reserve': 'Заповедник «Утриш»',
    'canonicalLocation.Kerch Strait': 'Керченский пролив',
    'canonicalLocation.Black Sea': 'Чёрное море',
    'canonicalLocation.Krasnodar Krai': 'Краснодарский край',
    'canonicalLocation.Crimea': 'Крым',
  },

  en: {
    'site.title': 'Black Sea Eco Monitor',
    'site.eyebrow': 'ENVIRONMENTAL INTELLIGENCE',
    'site.description': 'Environmental incidents map for the Black Sea region',

    'language.label': 'Interface language',
    'language.ru': 'Русский',
    'language.en': 'English',

    'connection.connecting': 'Connecting…',
    'connection.waiting': 'Waiting for API',
    'connection.online': 'Monitor online',
    'connection.updated': 'Updated {time}',
    'connection.offline': 'Monitor offline',
    'connection.lastKnown': 'Showing last known data · Updated {time}',
    'connection.unavailable': 'Monitor unavailable',

    'filters.aria': 'Event filters',
    'filters.kicker': 'FILTERS',
    'filters.title': 'Incident view',
    'filters.reset': 'Reset',
    'filters.status': 'STATUS',
    'filters.category': 'CATEGORY',
    'filters.moreCategories': 'More categories',
    'filters.timeWindow': 'TIME WINDOW',
    'filters.timeWindowAria': 'Time window',
    'filters.24h': '24H',
    'filters.7d': '7D',
    'filters.30d': '30D',
    'filters.all': 'ALL',
    'filters.timeNote': 'Time window prefers incident time, then source publication and detection time.',

    'status.detected': 'Detected',
    'status.active': 'Active',
    'status.contained': 'Contained',
    'status.resolved': 'Resolved',
    'status.unknown': 'Unknown',

    'severity.low': 'Low',
    'severity.medium': 'Medium',
    'severity.high': 'High',
    'severity.unknown': 'Unknown',

    'category.wildfire': 'Wildfire',
    'category.industrial_fire': 'Industrial fire',
    'category.oil_spill': 'Oil spill',
    'category.water_pollution': 'Water pollution',
    'category.algae_bloom': 'Algae bloom',
    'category.marine_animal_death': 'Marine animal death',
    'category.chemical_release': 'Chemical release',
    'category.storm_damage': 'Storm damage',
    'category.unknown': 'Environmental incident',

    'legend.aria': 'Event legend',
    'legend.title': 'INCIDENTS',

    'map.aria': 'Black Sea environmental incidents map',
    'map.zoomIn': 'Zoom in',
    'map.zoomOut': 'Zoom out',
    'map.resetBearing': 'Reset bearing',
    'map.attribution': 'Map attribution',
    'map.incidentsShort': 'INCIDENTS',
    'map.groupAria': '{count} incidents at {location}',

    'panel.aria': 'Selected event details',
    'panel.close': 'Close event details',
    'panel.eventConfidence': 'EVENT CONFIDENCE',
    'panel.locationConfidence': 'LOCATION CONFIDENCE',
    'panel.evidence': 'EVIDENCE',
    'panel.coordinates': 'COORDINATES',
    'panel.locationQuality': 'LOCATION QUALITY',
    'panel.locationType': 'LOCATION TYPE',
    'panel.mapScope': 'MAP SCOPE',
    'panel.coordinateSource': 'COORDINATE SOURCE',
    'panel.timeline': 'TIMELINE',
    'panel.incidentTime': 'INCIDENT TIME',
    'panel.sourceTime': 'SOURCE TIME',
    'panel.detected': 'DETECTED',
    'panel.firstSeen': 'FIRST SEEN',
    'panel.latest': 'LATEST',
    'panel.evidenceHeading': 'EVIDENCE · {count}',
    'panel.loadingSources': 'Loading sources…',
    'panel.noEvidence': 'No evidence records.',
    'panel.untitledSource': 'Untitled source',
    'panel.unknownSource': 'Unknown source',
    'panel.openSource': 'Open source ↗',
    'panel.evidenceUnavailable': 'Evidence unavailable: {message}',

    'group.kicker': 'CO-LOCATED INCIDENTS',
    'group.summary': '{count} share this canonical map point. Select one to inspect its evidence and lifecycle.',
    'group.back': '← {count} at this point',
    'group.cardMeta': 'Severity: {severity} · Confidence: {confidence} · Evidence: {evidence}',

    'location.unknown': 'Unknown location',
    'headline.fallback': 'Environmental incident',

    'locationType.city': 'City',
    'locationType.settlement': 'Settlement',
    'locationType.district': 'District',
    'locationType.street': 'Street',
    'locationType.facility': 'Facility',
    'locationType.protected_area': 'Protected Area',
    'locationType.coastal_area': 'Coastal Area',
    'locationType.water_body': 'Water Body',
    'locationType.region': 'Region',
    'locationType.other': 'Other',
    'locationType.unknown': 'Unknown',

    'locationScope.city': 'City-level',
    'locationScope.settlement': 'Settlement-level',
    'locationScope.district': 'District-level',
    'locationScope.street': 'Street-level',
    'locationScope.facility': 'Facility-level',
    'locationScope.protected_area': 'Protected-area',
    'locationScope.coastal_area': 'Coastal-area',
    'locationScope.water_body': 'Water-body',
    'locationScope.region': 'Region-level',
    'locationScope.other': 'Approximate',
    'locationScope.unknown': 'Unknown',

    'coordinateSource.canonical_database': 'Canonical Database',
    'coordinateSource.geocoded_address': 'Geocoded Address',
    'coordinateSource.llm_extraction': 'LLM Extraction',
    'coordinateSource.manual_review': 'Manual Review',
    'coordinateSource.satellite_detection': 'Satellite Detection',
    'coordinateSource.unknown': 'Unknown',

    'coordinateNote.canonical': 'Representative map point — not exact incident coordinates.',
    'coordinateNote.provenance': 'Coordinates include source provenance; verify precision before field use.',
    'coordinateNote.unknown': 'Coordinate provenance is unavailable.',

    'eventCount.one': '{count} event',
    'eventCount.few': '{count} events',
    'eventCount.many': '{count} events',
    'eventCount.filtered': '{visible} of {total} events',

    'canonicalLocation.Novorossiysk': 'Novorossiysk',
    'canonicalLocation.Gelendzhik': 'Gelendzhik',
    'canonicalLocation.Anapa': 'Anapa',
    'canonicalLocation.Sochi': 'Sochi',
    'canonicalLocation.Sevastopol': 'Sevastopol',
    'canonicalLocation.Utrish Reserve': 'Utrish Reserve',
    'canonicalLocation.Kerch Strait': 'Kerch Strait',
    'canonicalLocation.Black Sea': 'Black Sea',
    'canonicalLocation.Krasnodar Krai': 'Krasnodar Krai',
    'canonicalLocation.Crimea': 'Crimea',
  },
};

export function normalizeLanguage(value) {
  const language = String(value ?? '').trim().toLowerCase();
  return SUPPORTED_LANGUAGES.includes(language)
    ? language
    : DEFAULT_LANGUAGE;
}

export function localeForLanguage(language) {
  return LOCALES[normalizeLanguage(language)];
}

export function t(language, key, params = {}) {
  const lang = normalizeLanguage(language);
  const template = TRANSLATIONS[lang]?.[key]
    ?? TRANSLATIONS.en?.[key]
    ?? key;

  return String(template).replace(
    /\{(\w+)\}/g,
    (_, name) => String(params[name] ?? `{${name}}`),
  );
}

export function categoryLabel(category, language) {
  const key = String(category ?? '').trim();
  return t(
    language,
    TRANSLATIONS.en[`category.${key}`]
      ? `category.${key}`
      : 'category.unknown',
  );
}

export function statusLabel(status, language) {
  const key = String(status ?? '').trim().toLowerCase();
  return t(
    language,
    TRANSLATIONS.en[`status.${key}`]
      ? `status.${key}`
      : 'status.unknown',
  );
}

export function severityLabel(severity, language) {
  const key = String(severity ?? '').trim().toLowerCase();
  return t(
    language,
    TRANSLATIONS.en[`severity.${key}`]
      ? `severity.${key}`
      : 'severity.unknown',
  );
}

export function locationTypeLabel(locationType, language) {
  const key = String(locationType ?? '').trim().toLowerCase();
  return t(
    language,
    TRANSLATIONS.en[`locationType.${key}`]
      ? `locationType.${key}`
      : 'locationType.unknown',
  );
}

export function locationScopeLabel(locationType, language) {
  const key = String(locationType ?? '').trim().toLowerCase();
  return t(
    language,
    TRANSLATIONS.en[`locationScope.${key}`]
      ? `locationScope.${key}`
      : 'locationScope.unknown',
  );
}

export function coordinateSourceLabel(source, language) {
  const key = String(source ?? '').trim().toLowerCase();
  return t(
    language,
    TRANSLATIONS.en[`coordinateSource.${key}`]
      ? `coordinateSource.${key}`
      : 'coordinateSource.unknown',
  );
}

export function localizeLocationName(name, language) {
  const text = String(name ?? '').trim();

  if (!text) {
    return t(language, 'location.unknown');
  }

  const key = `canonicalLocation.${text}`;

  return TRANSLATIONS.en[key]
    ? t(language, key)
    : text;
}

export function formatEventCount(visible, total, language) {
  const lang = normalizeLanguage(language);

  if (visible !== total) {
    return t(lang, 'eventCount.filtered', {
      visible,
      total,
    });
  }

  if (lang === 'en') {
    return t(
      lang,
      visible === 1
        ? 'eventCount.one'
        : 'eventCount.many',
      { count: visible },
    );
  }

  const mod10 = visible % 10;
  const mod100 = visible % 100;

  let key = 'eventCount.many';

  if (mod10 === 1 && mod100 !== 11) {
    key = 'eventCount.one';
  } else if (
    [2, 3, 4].includes(mod10)
    && ![12, 13, 14].includes(mod100)
  ) {
    key = 'eventCount.few';
  }

  return t(lang, key, { count: visible });
}

export function loadStoredLanguage(storage = globalThis.localStorage) {
  try {
    return normalizeLanguage(
      storage?.getItem('blackSeaEcoMonitor.language')
      ?? DEFAULT_LANGUAGE,
    );
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

export function saveLanguage(language, storage = globalThis.localStorage) {
  const normalized = normalizeLanguage(language);

  try {
    storage?.setItem(
      'blackSeaEcoMonitor.language',
      normalized,
    );
  } catch {
    // Browser storage may be unavailable in privacy modes.
  }

  return normalized;
}
