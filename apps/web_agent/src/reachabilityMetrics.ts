interface DomainMetrics {
  totalChecks: number;
  warningCount: number;
  infoCount: number;
  lastOutcome: 'ok' | 'warning' | 'info';
  lastMessage?: string;
  lastUpdated: string;
}

export type ReachabilityOutcome = 'ok' | 'warning' | 'info';

interface RecordResult {
  metrics: DomainMetrics;
  notice: string | null;
}

const STORAGE_KEY = 'avatReachabilityMetrics';

const readStorage = (): Record<string, DomainMetrics> => {
  if (typeof window === 'undefined' || !window.localStorage) {
    return {};
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return {};
    }

    const parsed = JSON.parse(raw) as Record<string, DomainMetrics>;
    if (parsed && typeof parsed === 'object') {
      return parsed;
    }
  } catch (error) {
    console.warn('[AVAT][reachability] Failed to read stored metrics', error);
  }

  return {};
};

const writeStorage = (data: Record<string, DomainMetrics>): void => {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.warn('[AVAT][reachability] Failed to persist metrics', error);
  }
};

const formatPercentage = (part: number, total: number): string => {
  if (total === 0) {
    return '0%';
  }

  return `${Math.round((part / total) * 100)}%`;
};

export const recordReachabilityOutcome = (
  url: string,
  outcome: ReachabilityOutcome,
  message?: string,
): RecordResult | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  let hostname: string;
  try {
    hostname = new URL(url).hostname;
  } catch {
    return null;
  }

  const storage = readStorage();
  const existing = storage[hostname] ?? {
    totalChecks: 0,
    warningCount: 0,
    infoCount: 0,
    lastOutcome: 'ok' as const,
    lastUpdated: new Date(0).toISOString(),
  };

  const updated: DomainMetrics = {
    ...existing,
    totalChecks: existing.totalChecks + 1,
    lastOutcome: outcome,
    lastUpdated: new Date().toISOString(),
    lastMessage: message ?? existing.lastMessage,
  };

  if (outcome === 'warning') {
    updated.warningCount += 1;
  } else if (outcome === 'info') {
    updated.infoCount += 1;
  }

  storage[hostname] = updated;
  writeStorage(storage);

  if (outcome === 'warning') {
    console.warn(
      `[AVAT][reachability] ${hostname}: ${updated.warningCount}/${updated.totalChecks} checks reported warnings`,
    );
  } else {
    console.info(
      `[AVAT][reachability] ${hostname}: ${outcome} (${updated.totalChecks} checks recorded)`,
    );
  }

  const warningRatio = updated.warningCount / updated.totalChecks;

  if (updated.totalChecks >= 3 && warningRatio >= 0.5) {
    const percentage = formatPercentage(updated.warningCount, updated.totalChecks);
    const noticeMessage = `Домен ${hostname} часто блокирует запросы (${percentage} проверок с предупреждениями). Рассмотрите альтернативные источники или ручную проверку.`;
    return {
      metrics: updated,
      notice: noticeMessage,
    };
  }

  return {
    metrics: updated,
    notice: null,
  };
};
