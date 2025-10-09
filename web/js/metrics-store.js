(function (global) {
  const DEFAULT_TTL = 60 * 1000; // 60 seconds caching window

  function getDefaultApiBase() {
    if (typeof global.API_BASE === "string" && global.API_BASE.trim()) {
      return global.API_BASE;
    }
    return global.location.hostname.includes("localhost")
      ? "http://localhost:8000"
      : "https://api.mapmystandards.ai";
  }

  function now() {
    return Date.now();
  }

  function isExpired(timestamp, ttl) {
    if (!timestamp) return true;
    return now() - timestamp > ttl;
  }

  function getToken() {
    return (
      global.localStorage?.getItem("access_token") ||
      global.localStorage?.getItem("mms:authToken") ||
      global.sessionStorage?.getItem("access_token") ||
      null
    );
  }

  async function fetchJson(url, { suppressErrors = false } = {}) {
    const token = getToken();
    const headers = { "Content-Type": "application/json" };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: "GET",
      headers,
      credentials: "include",
    });

    if (response.status === 204) {
      return {};
    }

    if (!response.ok) {
      const message = `Request to ${url} failed with ${response.status}`;
      if (!suppressErrors) {
        throw new Error(message);
      }
      console.warn(message);
      return {};
    }

    const text = await response.text();
    if (!text) {
      return {};
    }

    try {
      return JSON.parse(text);
    } catch (error) {
      if (!suppressErrors) {
        throw error;
      }
      console.warn(`Failed to parse JSON from ${url}`, error);
      return {};
    }
  }

  function toNumber(value, fallback = 0) {
    if (typeof value === "number" && !Number.isNaN(value)) {
      return value;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function inferEvidenceStats(coreMetrics, performanceMetrics, evidenceMap) {
    const mappedCount = toNumber(
      coreMetrics?.standards_mapped,
      evidenceMap?.counts?.standards_mapped ?? 0
    );
    const totalStandardsRaw =
      coreMetrics?.total_standards ?? evidenceMap?.counts?.total_standards;
    const totalStandards = typeof totalStandardsRaw === "number" && totalStandardsRaw > 0
      ? totalStandardsRaw
      : null;

    const coverageFromPerformance =
      typeof performanceMetrics?.coverage_percentage === "number"
        ? performanceMetrics.coverage_percentage
        : null;
    const coveragePercentage =
      coverageFromPerformance ?? evidenceMap?.coverage_percentage ?? 0;

    let highConfidenceCount = null;
    if (Array.isArray(evidenceMap?.standards) && evidenceMap.standards.length > 0) {
      highConfidenceCount = evidenceMap.standards.filter((standard) => {
        const avg = toNumber(standard?.avg_confidence, 0);
        return avg >= 0.75;
      }).length;
    }

    return {
      mappedCount,
      totalStandards,
      coveragePercentage,
      highConfidenceCount,
    };
  }

  const store = {
    API_BASE: getDefaultApiBase(),
    ttl: DEFAULT_TTL,
    _metrics: null,
    _metricsLoadedAt: 0,
    _metricsPromise: null,
    _evidenceMap: null,
    _evidenceLoadedAt: 0,
    _evidencePromise: null,
    _gapAnalysis: null,
    _gapLoadedAt: 0,
    _gapPromise: null,

    reset() {
      this._metrics = null;
      this._metricsLoadedAt = 0;
      this._metricsPromise = null;
      this._evidenceMap = null;
      this._evidenceLoadedAt = 0;
      this._evidencePromise = null;
      this._gapAnalysis = null;
      this._gapLoadedAt = 0;
      this._gapPromise = null;
    },

    async ensure(options = {}) {
      const opts = {
        force: false,
        includeEvidenceMap: false,
        includeGapAnalysis: false,
        ttl: this.ttl,
        ...options,
      };

      if (opts.force) {
        this._metricsLoadedAt = 0;
        if (opts.includeEvidenceMap) this._evidenceLoadedAt = 0;
        if (opts.includeGapAnalysis) this._gapLoadedAt = 0;
      }

      await this.ensureMetrics(opts);

      if (opts.includeEvidenceMap) {
        await this.ensureEvidenceMap(opts);
      }

      if (opts.includeGapAnalysis) {
        await this.ensureGapAnalysis(opts);
      }

      return this.snapshot();
    },

    async ensureMetrics(options = {}) {
      const ttl = options.ttl ?? this.ttl;
      if (!isExpired(this._metricsLoadedAt, ttl) && this._metrics) {
        return this._metrics;
      }
      if (this._metricsPromise) {
        return this._metricsPromise;
      }

      const url = `${this.API_BASE}/api/user/intelligence-simple/dashboard/metrics`;
      this._metricsPromise = fetchJson(url)
        .then((payload) => {
          const data = payload?.data || payload || {};
          const core = payload?.core_metrics || data?.core_metrics || {};
          const performance =
            payload?.performance_metrics || data?.performance_metrics || {};
          const account = payload?.account_info || data?.account_info || {};

          this._metrics = {
            raw: payload,
            data,
            core,
            performance,
            account,
          };
          this._metricsLoadedAt = now();
          this._metricsPromise = null;
          return this._metrics;
        })
        .catch((error) => {
          this._metricsPromise = null;
          throw error;
        });

      return this._metricsPromise;
    },

    async ensureEvidenceMap(options = {}) {
      const ttl = options.ttl ?? this.ttl;
      if (!isExpired(this._evidenceLoadedAt, ttl) && this._evidenceMap) {
        return this._evidenceMap;
      }
      if (this._evidencePromise) {
        return this._evidencePromise;
      }

      const url = `${this.API_BASE}/api/user/intelligence-simple/standards/evidence-map`;
      this._evidencePromise = fetchJson(url, { suppressErrors: options.suppressErrors })
        .then((payload) => {
          this._evidenceMap = { raw: payload, data: payload };
          this._evidenceLoadedAt = now();
          this._evidencePromise = null;
          return this._evidenceMap;
        })
        .catch((error) => {
          this._evidencePromise = null;
          throw error;
        });

      return this._evidencePromise;
    },

    async ensureGapAnalysis(options = {}) {
      const ttl = options.ttl ?? this.ttl;
      if (!isExpired(this._gapLoadedAt, ttl) && this._gapAnalysis) {
        return this._gapAnalysis;
      }
      if (this._gapPromise) {
        return this._gapPromise;
      }

      const url = `${this.API_BASE}/api/user/intelligence-simple/gaps/analysis`;
      this._gapPromise = fetchJson(url, { suppressErrors: options.suppressErrors })
        .then((payload) => {
          this._gapAnalysis = payload || {};
          this._gapLoadedAt = now();
          this._gapPromise = null;
          return this._gapAnalysis;
        })
        .catch((error) => {
          this._gapPromise = null;
          throw error;
        });

      return this._gapPromise;
    },

    snapshot() {
      const coreMetrics = this._metrics?.core || {};
      const performanceMetrics = this._metrics?.performance || {};
      const evidenceMap = this._evidenceMap?.data || null;
      const evidenceStats = inferEvidenceStats(
        coreMetrics,
        performanceMetrics,
        evidenceMap
      );

      return {
        metrics: this._metrics?.data || this._metrics || {},
        coreMetrics,
        performanceMetrics,
        accountInfo: this._metrics?.account || {},
        evidenceMap,
        evidenceStats,
        gapAnalysis: this._gapAnalysis,
        lastUpdated: this._metricsLoadedAt || 0,
      };
    },
  };

  global.A3EMetricsStore = store;
})(window);
