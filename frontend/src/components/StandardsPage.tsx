import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowPathIcon,
  BookOpenIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ArrowTopRightOnSquareIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import api from '../services/api';

type StandardRecord = {
  id: string;
  code: string;
  title: string;
  description?: string;
  level: string;
  accreditor: string;
};

type SearchRecord = {
  id: string;
  code: string;
  title: string;
  snippet?: string;
  category?: string;
  accreditor?: string;
};

type ExplorerItem = {
  id: string;
  code: string;
  title: string;
  description?: string;
  summary: string;
  level: string;
  accreditor: string;
  snippet?: string;
  source: 'catalog' | 'search';
};

type EvidenceMappingEntry = {
  filename: string;
  doc_type?: string;
  accreditor?: string;
  confidence?: number;
};

type EvidenceDocumentSummary = {
  filename: string;
  doc_type?: string;
  trust_score?: number;
  uploaded_at?: string;
};

const LEVEL_OPTIONS = [
  { value: 'standard', label: 'Standards' },
  { value: 'clause', label: 'Clauses' },
  { value: 'indicator', label: 'Indicators' },
];

const DEFAULT_ACCREDITORS = ['HLC', 'SACSCOC', 'MSCHE', 'WASC', 'NWCCU', 'NECHE'];
const PAGE_SIZE = 20;

const truncate = (value: string, max = 200) => {
  if (!value) return '';
  return value.length > max ? `${value.slice(0, max)}…` : value;
};

const formatConfidence = (value?: number | null) => {
  if (value === undefined || value === null) return null;
  const scaled = value > 1 ? value : value * 100;
  return `${Math.round(scaled)}%`;
};

const StandardsPage: React.FC = () => {
  const [accreditorOptions, setAccreditorOptions] = useState<{ code: string; name?: string; standard_count?: number; loaded_node_count?: number }[]>(
    DEFAULT_ACCREDITORS.map((code) => ({ code }))
  );
  const [selectedAccreditor, setSelectedAccreditor] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const cached = window.localStorage.getItem('primary_accreditor');
      if (cached) return cached.toUpperCase();
    }
    return 'HLC';
  });
  const [levels, setLevels] = useState<string[]>(['standard']);
  const [standards, setStandards] = useState<StandardRecord[]>([]);
  const [displayMode, setDisplayMode] = useState<'full' | 'redacted'>('full');
  const [listLoading, setListLoading] = useState<boolean>(false);
  const [listError, setListError] = useState<string>('');
  const [searchInput, setSearchInput] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [searchLoading, setSearchLoading] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchRecord[]>([]);
  const [page, setPage] = useState<number>(1);
  const [selectedItem, setSelectedItem] = useState<ExplorerItem | null>(null);
  const [coverageStats, setCoverageStats] = useState<{ coverage_percentage?: number; total_items?: number; covered_items?: number } | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState<boolean>(false);
  const [evidenceError, setEvidenceError] = useState<string>('');
  const [evidenceMap, setEvidenceMap] = useState<Record<string, EvidenceMappingEntry[]>>({});
  const [evidenceDocuments, setEvidenceDocuments] = useState<EvidenceDocumentSummary[]>([]);

  const levelsToken = useMemo(() => levels.slice().sort().join(','), [levels]);

  const trackExplorer = useCallback(
    (
      event: string,
      attrs: {
        result?: string;
        duration_ms?: number;
        error?: string;
        payload?: Record<string, any>;
        page?: number;
        page_size?: number;
        total_items?: number;
      } = {}
    ) => {
      api.telemetry
        .standardsExplorer({
          event,
          accreditor: selectedAccreditor,
          result: attrs.result,
          duration_ms: attrs.duration_ms,
          error: attrs.error,
          page: attrs.page,
          page_size: attrs.page_size,
          total_items: attrs.total_items,
          payload: attrs.payload,
        })
        .catch(() => {
          /* telemetry failures are non-blocking */
        });
    },
    [selectedAccreditor]
  );

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const { data } = await api.standards.getCorpusMetadata();
        if (data?.accreditors) {
          const next = (data.accreditors as any[]).map((item) => ({
            code: String(item.accreditor || item.name || '').toUpperCase(),
            name: item.name || item.accreditor,
            standard_count: item.standard_count,
            loaded_node_count: item.loaded_node_count,
          }));
          if (next.length) {
            setAccreditorOptions(next);
          }
        }
      } catch (err) {
        console.warn('Failed to load accreditor metadata', err);
      }
    };
    fetchMetadata();
  }, []);

  useEffect(() => {
    const handler = setTimeout(() => {
      setSearchTerm(searchInput.trim());
    }, 350);
    return () => clearTimeout(handler);
  }, [searchInput]);

  useEffect(() => {
    const fetchCoverage = async () => {
      try {
        const { data } = await api.standards.getChecklistStats({ accreditor: selectedAccreditor });
        setCoverageStats({
          coverage_percentage: data?.coverage_percentage,
          total_items: data?.total_items,
          covered_items: data?.covered_items,
        });
      } catch {
        setCoverageStats(null);
      }
    };
    fetchCoverage();
  }, [selectedAccreditor]);

  useEffect(() => {
    const loadEvidenceMap = async () => {
      setEvidenceLoading(true);
      setEvidenceError('');
      const started = typeof performance !== 'undefined' ? performance.now() : undefined;
      trackExplorer('evidence_map_load_start');
      try {
        const { data } = await api.standards.getEvidenceMap({ accreditor: selectedAccreditor });
        const mapping = (data?.mapping || {}) as Record<string, EvidenceMappingEntry[]>;
        setEvidenceMap(mapping);
        setEvidenceDocuments(Array.isArray(data?.documents) ? (data.documents as EvidenceDocumentSummary[]) : []);
        trackExplorer('evidence_map_load_success', {
          result: 'success',
          duration_ms: started ? Math.round(performance.now() - started) : undefined,
          total_items: Object.keys(mapping).length,
          payload: {
            documents: data?.counts?.documents,
            coverage_percentage: data?.coverage_percentage,
          },
        });
      } catch (err: any) {
        setEvidenceMap({});
        setEvidenceDocuments([]);
        const message = err?.response?.data?.detail || 'Linked evidence will appear after uploads are processed.';
        setEvidenceError(message);
        trackExplorer('evidence_map_load_error', {
          result: 'error',
          duration_ms: started ? Math.round(performance.now() - started) : undefined,
          error: err?.message || 'evidence_map_load_error',
          payload: { message },
        });
      } finally {
        setEvidenceLoading(false);
      }
    };
    loadEvidenceMap();
  }, [selectedAccreditor, trackExplorer]);

  useEffect(() => {
    const fetchStandards = async () => {
      setListLoading(true);
      setListError('');
      const started = typeof performance !== 'undefined' ? performance.now() : undefined;
      const levelsParam = levels.length === LEVEL_OPTIONS.length ? 'all' : levels.join(',');
      trackExplorer('catalog_load_start', {
        payload: { levels: levelsParam },
      });
      try {
        const { data } = await api.standards.listExplorer({ accreditor: selectedAccreditor, levels: levelsParam });
        const items: StandardRecord[] = (data?.standards || []).map((item: any) => ({
          id: String(item.id || item.code),
          code: String(item.code || item.id),
          title: item.title || item.code,
          description: item.description || '',
          level: String(item.level || 'standard').toLowerCase(),
          accreditor: (item.accreditor || selectedAccreditor || '').toUpperCase(),
        }));
        setStandards(items);
        setDisplayMode(data?.display_mode === 'redacted' ? 'redacted' : 'full');
        trackExplorer('catalog_load_success', {
          result: 'success',
          duration_ms: started ? Math.round(performance.now() - started) : undefined,
          total_items: items.length,
          payload: {
            display_mode: data?.display_mode,
            coverage: data?.coverage_percentage,
            levels: levelsParam,
          },
        });
      } catch (err: any) {
        console.error('Failed to load standards catalog', err);
        setStandards([]);
        setListError('Unable to load the standards catalog right now.');
        trackExplorer('catalog_load_error', {
          result: 'error',
          duration_ms: started ? Math.round(performance.now() - started) : undefined,
          error: err?.message || 'catalog_load_error',
          payload: { message: err?.response?.data?.detail, levels: levelsParam },
        });
      } finally {
        setListLoading(false);
      }
    };
    fetchStandards();
    window.localStorage.setItem('primary_accreditor', selectedAccreditor);
    setPage(1);
  }, [selectedAccreditor, levelsToken, levels, trackExplorer]);

  useEffect(() => {
    if (!searchTerm) {
      setSearchResults([]);
      setSearchError('');
      setSearchLoading(false);
      return;
    }
    let cancelled = false;
    const fetchSearch = async () => {
      setSearchLoading(true);
      setSearchError('');
      const started = typeof performance !== 'undefined' ? performance.now() : undefined;
      trackExplorer('catalog_search_start', {
        payload: { term: searchTerm, accreditor: selectedAccreditor },
      });
      try {
        const { data } = await api.standards.search({ q: searchTerm, accreditor: selectedAccreditor });
        const next: SearchRecord[] = (data?.results || []).map((item: any) => ({
          id: String(item.id || item.code),
          code: String(item.code || item.id),
          title: item.title || item.code,
          snippet: item.snippet,
          category: (item.category || 'standard').toLowerCase(),
          accreditor: (item.accreditor || selectedAccreditor || '').toUpperCase(),
        }));
        if (!cancelled) {
          const allowedLevels = new Set(levels.map((l) => l.toLowerCase()));
          setSearchResults(
            levels.length === LEVEL_OPTIONS.length
              ? next
              : next.filter((item) => allowedLevels.has(item.category || 'standard'))
          );
          trackExplorer('catalog_search_success', {
            result: 'success',
            duration_ms: started ? Math.round(performance.now() - started) : undefined,
            total_items: next.length,
            payload: { term: searchTerm, levels: Array.from(levels), accreditor: selectedAccreditor },
          });
        }
      } catch (err: any) {
        if (!cancelled) {
          console.error('Standards search failed', err);
          setSearchResults([]);
          setSearchError('Search failed. Please try again.');
          trackExplorer('catalog_search_error', {
            result: 'error',
            duration_ms: started ? Math.round(performance.now() - started) : undefined,
            error: err?.message || 'catalog_search_error',
            payload: { term: searchTerm, accreditor: selectedAccreditor },
          });
        }
      } finally {
        if (!cancelled) {
          setSearchLoading(false);
          setPage(1);
        }
      }
    };
    fetchSearch();
    return () => {
      cancelled = true;
    };
  }, [searchTerm, selectedAccreditor, levelsToken, levels, trackExplorer]);

  const standardsMap = useMemo(() => {
    const map = new Map<string, StandardRecord>();
    standards.forEach((item) => {
      map.set(item.id || item.code, item);
    });
    return map;
  }, [standards]);

  const baseItems = useMemo<ExplorerItem[]>(() => {
    if (searchTerm) {
      return searchResults.map((result) => {
        const catalog = standardsMap.get(result.id) || standardsMap.get(result.code);
        const level = (result.category || catalog?.level || 'standard').toLowerCase();
        const description = catalog?.description || '';
        const summarySource = result.snippet || description;
        return {
          id: result.id,
          code: result.code,
          title: result.title,
          description: description || undefined,
          summary: summarySource ? truncate(summarySource, 220) : 'Summary unavailable (redacted corpus).',
          level,
          accreditor: (result.accreditor || catalog?.accreditor || selectedAccreditor).toUpperCase(),
          snippet: result.snippet,
          source: 'search',
        };
      });
    }
    return standards.map((item) => ({
      id: item.id,
      code: item.code,
      title: item.title,
      description: item.description,
      summary: item.description ? truncate(item.description, 220) : 'Description unavailable for this node.',
      level: item.level,
      accreditor: item.accreditor?.toUpperCase() || selectedAccreditor,
      source: 'catalog',
    }));
  }, [searchResults, standards, searchTerm, standardsMap, selectedAccreditor]);

  const levelSet = useMemo(() => new Set(levels.map((l) => l.toLowerCase())), [levels]);

  const filteredItems = useMemo(() => {
    if (levels.length === LEVEL_OPTIONS.length) return baseItems;
    return baseItems.filter((item) => levelSet.has(item.level || 'standard'));
  }, [baseItems, levelSet, levels.length]);

  const totalResults = filteredItems.length;
  const totalPages = Math.max(1, Math.ceil(totalResults / PAGE_SIZE));
  const paginatedItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filteredItems.slice(start, start + PAGE_SIZE);
  }, [filteredItems, page]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  useEffect(() => {
    if (!filteredItems.length) {
      setSelectedItem(null);
      return;
    }
    setSelectedItem((prev) => {
      if (prev && filteredItems.some((item) => item.id === prev.id)) {
        return filteredItems.find((item) => item.id === prev.id) || filteredItems[0];
      }
      return filteredItems[0];
    });
  }, [filteredItems]);

  const selectedAccreditorMeta = accreditorOptions.find((item) => item.code === selectedAccreditor);

  const linkedEvidence = useMemo(() => {
    if (!selectedItem) return [] as EvidenceMappingEntry[];
    const byId = evidenceMap[selectedItem.id];
    if (byId && byId.length) return byId;
    const byCode = evidenceMap[selectedItem.code];
    return byCode || [];
  }, [selectedItem, evidenceMap]);
  const hasLinkedEvidence = linkedEvidence.length > 0;
  const evidenceDocumentsCount = evidenceDocuments.length;
  const crosswalkLink = useMemo(() => {
    if (!selectedItem) return '';
    const params = new URLSearchParams({
      standard: selectedItem.id,
      accreditor: selectedItem.accreditor,
    });
    return `/crosswalk?${params.toString()}`;
  }, [selectedItem]);
  const reviewerPackLink = useMemo(() => {
    if (!selectedItem) return '';
    const params = new URLSearchParams({
      standard_id: selectedItem.id,
      accreditor: selectedItem.accreditor,
    });
    return `/reports?${params.toString()}`;
  }, [selectedItem]);

  const toggleLevel = (value: string) => {
    setLevels((prev) => {
      if (prev.includes(value)) {
        return prev.filter((v) => v !== value);
      }
      return [...prev, value];
    });
  };

  const resetFilters = () => {
    setLevels(['standard']);
    setSearchInput('');
    setSearchTerm('');
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Standards Explorer</h1>
          <p className="mt-2 text-sm text-gray-600">
            Browse the full accreditation corpus, compare frameworks, and surface the exact clauses you need without relying on mapped documents.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Accreditor</label>
          <select
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none"
            value={selectedAccreditor}
            onChange={(event) => {
              setSelectedAccreditor(event.target.value.toUpperCase());
            }}
          >
            {accreditorOptions.map((option) => (
              <option key={option.code} value={option.code}>
                {option.code}
              </option>
            ))}
          </select>
        </div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Catalog Size</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">{standards.length}</span>
            <span className="text-sm text-gray-500">loaded nodes</span>
          </div>
          {selectedAccreditorMeta?.standard_count ? (
            <p className="mt-2 text-xs text-gray-500">{selectedAccreditorMeta.standard_count} total expected for {selectedAccreditor}</p>
          ) : null}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Viewing</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">{totalResults}</span>
            <span className="text-sm text-gray-500">results</span>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {searchTerm ? 'Search matches across the corpus.' : 'Filtered selection from the loaded catalog.'}
          </p>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Levels</div>
          <div className="mt-2 text-lg font-semibold text-gray-900">{levels.length === LEVEL_OPTIONS.length ? 'All levels' : levels.map((l) => l[0].toUpperCase() + l.slice(1)).join(', ')}</div>
          <p className="mt-2 text-xs text-gray-500">Toggle clauses and indicators to broaden the explorer view.</p>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Mapped Coverage</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">{coverageStats ? coverageStats.coverage_percentage?.toFixed(1) ?? '0.0' : '--'}</span>
            <span className="text-sm text-gray-500">%</span>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {coverageStats
              ? `${coverageStats.covered_items || 0} of ${coverageStats.total_items || 0} items currently mapped`
              : 'Upload evidence to populate personalized coverage.'}
          </p>
          {evidenceDocumentsCount > 0 ? (
            <p className="mt-1 text-xs text-gray-500">{evidenceDocumentsCount} evidence files contributing to this map.</p>
          ) : null}
        </div>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search by code, keyword, or requirement…"
              className="w-full rounded-md border border-gray-300 py-2 pl-10 pr-4 text-sm shadow-sm focus:border-primary-500 focus:outline-none"
            />
            {searchTerm && (
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold uppercase tracking-wide text-primary-600 hover:text-primary-700"
                onClick={() => {
                  setSearchInput('');
                  setSearchTerm('');
                }}
              >
                Clear
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <FunnelIcon className="h-4 w-4" />
              <span>Levels</span>
            </div>
            {LEVEL_OPTIONS.map((option) => (
              <label key={option.value} className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  checked={levels.includes(option.value)}
                  onChange={() => toggleLevel(option.value)}
                />
                {option.label}
              </label>
            ))}
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:border-gray-300 hover:text-gray-900"
              onClick={resetFilters}
            >
              <ArrowPathIcon className="h-4 w-4" /> Reset
            </button>
          </div>
        </div>

        {(searchLoading || listLoading) && (
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
            <span className="h-3 w-3 animate-spin rounded-full border-2 border-gray-400 border-t-transparent" />
            <span>{searchLoading ? 'Searching across frameworks…' : 'Loading standards catalog…'}</span>
          </div>
        )}

        {(searchError || listError) && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {searchError || listError}
          </div>
        )}
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          {paginatedItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center text-sm text-gray-500">
              <BookOpenIcon className="h-10 w-10 text-gray-300" />
              <p>No standards match the current filters.</p>
              <p className="text-xs text-gray-400">Try adjusting accreditor, levels, or clearing your search.</p>
            </div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {paginatedItems.map((item) => {
                const isActive = selectedItem?.id === item.id;
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedItem(item)}
                      className={`block w-full text-left transition-colors ${
                        isActive ? 'bg-primary-50/60' : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex flex-col gap-2 px-4 py-3">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="rounded-md bg-gray-100 px-2 py-0.5 text-xs font-mono text-gray-600">{item.code}</span>
                            <span className="text-sm font-semibold text-gray-900">{item.title}</span>
                          </div>
                          <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-wide text-gray-500">
                            <span>{item.accreditor}</span>
                            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-600">{item.level}</span>
                            <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-600">{item.source === 'search' ? 'Search match' : 'Catalog'}</span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600">{item.summary}</p>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3 text-sm text-gray-500">
            <div>Page {page} of {totalPages}</div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={page === 1}
                className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-3 py-1 text-sm font-medium text-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <ChevronLeftIcon className="h-4 w-4" /> Prev
              </button>
              <button
                type="button"
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={page === totalPages}
                className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-3 py-1 text-sm font-medium text-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next <ChevronRightIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <aside className="flex h-full flex-col gap-4 rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Standard Detail</h2>
          {!selectedItem ? (
            <p className="text-sm text-gray-500">Select a standard from the list to view full context.</p>
          ) : (
            <div className="space-y-4">
              <div className="space-y-1">
                <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Standard</div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-md bg-gray-100 px-2 py-0.5 font-mono text-sm text-gray-700">{selectedItem.code}</span>
                  <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-indigo-600">{selectedItem.level}</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-900">{selectedItem.title}</h3>
              </div>

              <div className="rounded-md border border-gray-100 bg-gray-50 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Accreditor: <span className="ml-2 text-gray-900">{selectedItem.accreditor}</span>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-gray-800">Description</h4>
                {displayMode === 'redacted' && !selectedItem.description ? (
                  <p className="text-sm text-gray-500">
                    Detailed descriptions are redacted for this corpus in the current environment. Contact support to enable full-text visibility.
                  </p>
                ) : (
                  <p className="whitespace-pre-line text-sm text-gray-700">
                    {selectedItem.description || selectedItem.summary || 'Description coming soon.'}
                  </p>
                )}
              </div>

              {selectedItem.snippet && (
                <div className="rounded-md border border-primary-100 bg-primary-50 px-3 py-2 text-sm text-primary-700">
                  <div className="text-xs font-semibold uppercase tracking-wide">Search snippet</div>
                  <p className="mt-1">{selectedItem.snippet}</p>
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-gray-800">Linked evidence</h4>
                  {evidenceLoading ? (
                    <span className="flex items-center gap-1 text-xs text-gray-400">
                      <span className="h-3 w-3 animate-spin rounded-full border border-gray-300 border-t-transparent" />
                      Loading…
                    </span>
                  ) : hasLinkedEvidence ? (
                    <span className="text-xs uppercase tracking-wide text-emerald-600">{linkedEvidence.length} matches</span>
                  ) : null}
                </div>
                {hasLinkedEvidence ? (
                  <ul className="space-y-2">
                    {linkedEvidence.map((entry, index) => {
                      const confidenceLabel = formatConfidence(entry.confidence);
                      return (
                        <li
                          key={`${entry.filename || 'evidence'}-${index}`}
                          className="rounded-md border border-gray-100 bg-gray-50 p-3"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate text-sm font-medium text-gray-800" title={entry.filename}>
                              {entry.filename || 'Evidence file'}
                            </span>
                            {confidenceLabel ? (
                              <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
                                {confidenceLabel}
                              </span>
                            ) : null}
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                            {entry.doc_type ? (
                              <span className="rounded-md border border-gray-200 bg-white px-2 py-0.5">{entry.doc_type}</span>
                            ) : null}
                            {entry.accreditor ? (
                              <span className="rounded-md border border-gray-200 bg-white px-2 py-0.5">{entry.accreditor}</span>
                            ) : null}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">
                    {evidenceError || 'Once you upload evidence, linked documents will surface here automatically.'}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-gray-800">Quick actions</h4>
                <div className="space-y-2">
                  <Link
                    to={crosswalkLink || '#'}
                    className="flex items-center justify-between gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-primary-600 transition hover:border-primary-200 hover:bg-primary-50/60"
                  >
                    <span>View mappings in CrosswalkX</span>
                    <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                  </Link>
                  <Link
                    to={hasLinkedEvidence ? reviewerPackLink : '/documents'}
                    className={`flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm font-medium transition ${
                      hasLinkedEvidence
                        ? 'border-primary-200 text-primary-600 hover:bg-primary-50/60'
                        : 'border-gray-200 text-gray-400 hover:border-gray-300'
                    }`}
                    aria-disabled={!hasLinkedEvidence}
                  >
                    <span>{hasLinkedEvidence ? 'Build reviewer pack with this standard' : 'Upload evidence to enable pack shortcuts'}</span>
                    <DocumentDuplicateIcon className="h-4 w-4" />
                  </Link>
                </div>
                {!hasLinkedEvidence ? (
                  <p className="text-xs text-gray-400">
                    Upload supporting evidence to unlock reviewer pack exports tailored to this requirement.
                  </p>
                ) : null}
              </div>

              <div className="text-xs text-gray-400">Source: {selectedItem.source === 'search' ? 'Search results' : 'Corpus catalog'} · Display mode: {displayMode}</div>
            </div>
          )}
        </aside>
      </section>
    </div>
  );
};

export default StandardsPage;
