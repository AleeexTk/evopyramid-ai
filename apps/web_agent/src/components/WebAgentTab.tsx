import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { recordReachabilityOutcome } from '../reachabilityMetrics';
import type { AgentMessage, WebAgentTabState } from '../types';

type TabStatus = 'idle' | 'checking' | 'loading';

type ReachabilityTone = 'info' | 'warning';

interface ReachabilityFeedback {
  tone: ReachabilityTone;
  message: string;
}

type UrlValidationResult =
  | { ok: true; value: string; normalized: boolean }
  | { ok: false; error: string };

const addHttpsScheme = (candidate: string): string => {
  if (/^https?:\/\//i.test(candidate)) {
    return candidate;
  }

  return `https://${candidate}`;
};

const validateHttpUrl = (candidate: string): UrlValidationResult => {
  const trimmed = candidate.trim();
  if (!trimmed) {
    return { ok: false, error: 'Введите адрес страницы, чтобы продолжить.' };
  }

  const attempts: Array<{ value: string; normalized: boolean }> = [
    { value: trimmed, normalized: false },
  ];

  if (!/^https?:\/\//i.test(trimmed)) {
    attempts.push({ value: addHttpsScheme(trimmed), normalized: true });
  }

  for (const attempt of attempts) {
    try {
      const url = new URL(attempt.value);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        return {
          ok: false,
          error: 'Неверный протокол. Используйте адрес, начинающийся с http:// или https://.',
        };
      }

      return { ok: true, value: url.toString(), normalized: attempt.normalized };
    } catch (error) {
      // Продолжим попытки, если схема была добавлена автоматически.
    }
  }

  return {
    ok: false,
    error: 'Неверный формат URL. Проверьте адрес и попробуйте снова.',
  };
};

const createTimestampLabel = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

const roleLabel: Record<AgentMessage['role'], string> = {
  user: 'Пользователь',
  assistant: 'AVAT',
  system: 'Система',
};

const REACHABILITY_TIMEOUT_MS = 5000;

const checkUrlReachability = async (url: string): Promise<ReachabilityFeedback | null> => {
  if (typeof window === 'undefined' || typeof fetch === 'undefined') {
    return null;
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REACHABILITY_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      method: 'HEAD',
      mode: 'cors',
      redirect: 'follow',
      signal: controller.signal,
    });

    if (response.ok) {
      return null;
    }

    if (response.status === 405 || response.status === 501) {
      return {
        tone: 'info',
        message:
          'Сервер не поддерживает проверку HEAD. Страница будет загружена, но доступность не подтверждена.',
      };
    }

    return {
      tone: 'warning',
      message: `Сервер ответил со статусом ${response.status}. Страница может быть недоступна или требовать авторизации.`,
    };
  } catch (error) {
    const errorName = (error as DOMException | undefined)?.name;
    if (errorName === 'AbortError') {
      return {
        tone: 'warning',
        message: 'Проверка доступности заняла слишком много времени. Страница может не отвечать.',
      };
    }

    return {
      tone: 'info',
      message:
        'Не удалось проверить доступность страницы. Возможны сетевые ограничения или политика CORS.',
    };
  } finally {
    window.clearTimeout(timeoutId);
  }
};

export interface WebAgentTabProps {
  tab: WebAgentTabState;
  onNavigate: (tabId: string, url: string) => void;
  onSendMessage: (tabId: string, message: string) => void;
  onToggleMonitor: (tabId: string) => void;
  onUpdateTab: (tabId: string, updates: Partial<WebAgentTabState>) => void;
}

export function WebAgentTab({
  tab,
  onNavigate,
  onSendMessage,
  onToggleMonitor,
  onUpdateTab,
}: WebAgentTabProps) {
  const [addressValue, setAddressValue] = useState(() => tab.url ?? '');
  const [messageDraft, setMessageDraft] = useState('');
  const [status, setStatus] = useState<TabStatus>('idle');
  const [localError, setLocalError] = useState<string | null>(null);
  const [reachabilityFeedback, setReachabilityFeedback] = useState<ReachabilityFeedback | null>(null);
  const [aggregateNotice, setAggregateNotice] = useState<string | null>(null);
  const navigationCheckRef = useRef(0);
  const idleTimeoutRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    setAddressValue(tab.url ?? '');
  }, [tab.url]);

  useEffect(() => {
    if (typeof tab.error === 'string' && tab.error.length > 0) {
      setLocalError(tab.error);
    } else {
      setLocalError(null);
    }
  }, [tab.error]);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (idleTimeoutRef.current !== null) {
        window.clearTimeout(idleTimeoutRef.current);
        idleTimeoutRef.current = null;
      }
    };
  }, []);

  const handleNavigate = useCallback(async () => {
    const result = validateHttpUrl(addressValue);

    if (!result.ok) {
      setLocalError(result.error);
      onUpdateTab(tab.id, { error: result.error });
      setReachabilityFeedback(null);
      return;
    }

    if (idleTimeoutRef.current !== null) {
      window.clearTimeout(idleTimeoutRef.current);
      idleTimeoutRef.current = null;
    }

    const currentCheckId = navigationCheckRef.current + 1;
    navigationCheckRef.current = currentCheckId;

    setStatus('checking');
    setLocalError(null);
    setReachabilityFeedback(null);
    if (result.normalized) {
      setAddressValue(result.value);
    }

    const feedback = await checkUrlReachability(result.value);

    if (!isMountedRef.current || navigationCheckRef.current !== currentCheckId) {
      return;
    }

    const outcome = feedback ? (feedback.tone === 'warning' ? 'warning' : 'info') : 'ok';
    const aggregateResult = recordReachabilityOutcome(result.value, outcome, feedback?.message);

    if (aggregateResult?.notice ?? false) {
      setAggregateNotice(aggregateResult.notice);
    } else {
      setAggregateNotice(null);
    }

    if (feedback) {
      setReachabilityFeedback(feedback);
    }

    setStatus('loading');
    onUpdateTab(tab.id, { error: undefined, url: result.value });
    onNavigate(tab.id, result.value);

    idleTimeoutRef.current = window.setTimeout(() => {
      if (!isMountedRef.current || navigationCheckRef.current !== currentCheckId) {
        return;
      }
      setStatus('idle');
    }, 250);
  }, [addressValue, onNavigate, onUpdateTab, tab.id]);

  const handleSubmit = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      handleNavigate();
    },
    [handleNavigate],
  );

  const handleMessageSend = useCallback(() => {
    const draft = messageDraft.trim();
    if (!draft) {
      return;
    }

    onSendMessage(tab.id, draft);
    setMessageDraft('');
  }, [messageDraft, onSendMessage, tab.id]);

  const statusLabel = useMemo(() => {
    if (status === 'checking') {
      return 'Проверка доступности…';
    }
    if (status === 'loading') {
      return 'Загрузка…';
    }
    return tab.isMonitoring ? 'Мониторинг активен' : 'Ожидание действий';
  }, [status, tab.isMonitoring]);

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="space-y-2 rounded-lg border border-slate-700 bg-slate-900/60 p-4 shadow">
        <form className="flex items-center gap-2" onSubmit={handleSubmit}>
          <input
            value={addressValue}
            onChange={(event) => {
              setAddressValue(event.target.value);
              if (localError) {
                setLocalError(null);
                onUpdateTab(tab.id, { error: undefined });
              }
              if (reachabilityFeedback) {
                setReachabilityFeedback(null);
              }
              if (aggregateNotice) {
                setAggregateNotice(null);
              }
            }}
            placeholder="https://example.com"
            type="url"
            inputMode="url"
            className={`flex-1 rounded-md border px-3 py-2 text-sm text-slate-100 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
              localError
                ? 'border-rose-500 focus:ring-rose-400'
                : 'border-slate-700 bg-slate-950/60 focus:border-emerald-500'
            }`}
            aria-invalid={localError ? 'true' : 'false'}
            aria-describedby={localError ? `tab-${tab.id}-url-error` : undefined}
          />
          <button
            type="submit"
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 shadow transition hover:bg-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            Загрузить
          </button>
          <button
            type="button"
            onClick={() => onToggleMonitor(tab.id)}
            className={`rounded-md px-4 py-2 text-sm font-medium shadow transition focus:outline-none focus:ring-2 ${
              tab.isMonitoring
                ? 'bg-amber-500 text-amber-950 hover:bg-amber-400 focus:ring-amber-500'
                : 'bg-slate-800 text-slate-100 hover:bg-slate-700 focus:ring-slate-500'
            }`}
          >
            {tab.isMonitoring ? 'Остановить мониторинг' : 'Мониторить'}
          </button>
        </form>
        {localError ? (
          <p
            id={`tab-${tab.id}-url-error`}
            className="text-sm font-medium text-rose-400"
            role="alert"
            aria-live="assertive"
          >
            {localError}
          </p>
        ) : null}
        <p className="text-xs text-slate-400" aria-live="polite">
          {statusLabel}
        </p>
        {reachabilityFeedback ? (
          <p
            className={`text-xs ${
              reachabilityFeedback.tone === 'warning' ? 'text-amber-400' : 'text-slate-300'
            }`}
            role="status"
            aria-live="polite"
          >
            {reachabilityFeedback.message}
          </p>
        ) : null}
        {aggregateNotice ? (
          <p className="text-xs text-amber-300" role="status" aria-live="polite">
            {aggregateNotice}
          </p>
        ) : null}
      </div>

      <div className="flex-1 space-y-3 overflow-hidden rounded-lg border border-slate-800 bg-slate-950/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Журнал взаимодействия</h2>
        <div className="h-64 overflow-y-auto rounded-md border border-slate-800 bg-slate-900/40 p-3 text-sm text-slate-100">
          {tab.messages.length === 0 ? (
            <p className="text-slate-400">Пока нет сообщений. Задайте вопрос агенту AVAT.</p>
          ) : (
            <ul className="space-y-3">
              {tab.messages.map((message) => (
                <li key={message.id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span className="font-medium text-slate-200">{roleLabel[message.role]}</span>
                    <span>{createTimestampLabel(message.timestamp)}</span>
                  </div>
                  <div className="whitespace-pre-wrap rounded-md bg-slate-900/70 p-3 text-sm text-slate-100">
                    {message.content}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="space-y-2">
          <label htmlFor={`tab-${tab.id}-message`} className="text-xs font-medium text-slate-400">
            Новое сообщение
          </label>
          <textarea
            id={`tab-${tab.id}-message`}
            value={messageDraft}
            onChange={(event) => setMessageDraft(event.target.value)}
            rows={3}
            className="w-full rounded-md border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="Опишите задачу для агента AVAT"
          />
          <div className="flex items-center justify-end">
            <button
              type="button"
              onClick={handleMessageSend}
              disabled={messageDraft.trim().length === 0}
              className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-emerald-950 shadow transition hover:bg-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-900/40 disabled:text-emerald-100/60"
            >
              Отправить
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
