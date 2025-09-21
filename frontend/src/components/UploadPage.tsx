import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import api from '../services/api';
import UploadHelp from './guides/UploadHelp';

type RecentItem = {
  job_id: string;
  file_id: string;
  filename: string;
  file_size: number;
  status: string;
  progress: number;
  uploaded_at: string;
  updated_at: string;
};

const prettyBytes = (n: number) => {
  if (!n) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0; let v = n;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${units[i]}`;
};

const UploadPage: React.FC = () => {
  const [dragOver, setDragOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [lastJob, setLastJob] = useState<any>(null);
  const [recent, setRecent] = useState<RecentItem[]>([]);
  const [error, setError] = useState<string>('');
  const pollRef = useRef<number | null>(null);

  const fetchRecent = useCallback(async () => {
    try {
      const { data } = await api.uploads.recent(10);
      if (data?.success && data?.data?.uploads) setRecent(data.data.uploads);
    } catch { /* no-op */ }
  }, []);

  useEffect(() => { fetchRecent(); }, [fetchRecent]);

  const startPolling = useCallback((jobId: string) => {
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      try {
        const { data } = await api.uploads.getJob(jobId);
        if (data?.success) {
          setLastJob(data.data);
          if (['completed', 'failed'].includes(data.data.status)) {
            if (pollRef.current) window.clearInterval(pollRef.current);
            pollRef.current = null;
            fetchRecent();
          }
        }
      } catch { /* ignore */ }
    }, 1500) as unknown as number;
  }, [fetchRecent]);

  useEffect(() => () => { if (pollRef.current) window.clearInterval(pollRef.current); }, []);

  const onFiles = useCallback(async (files: FileList | null) => {
    if (!files || !files.length) return;
    setError(''); setBusy(true);
    try {
      const f = files[0];
      const { data } = await api.uploads.upload(f, { title: f.name });
      if (data?.success && data?.data?.job_id) {
        setLastJob({ job_id: data.data.job_id, status: data.data.status, filename: data.data.filename, progress: 0 });
        startPolling(data.data.job_id);
      } else {
        setError('Upload failed.');
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Upload failed.');
    } finally { setBusy(false); }
  }, [startPolling]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setDragOver(false);
    onFiles(e.dataTransfer.files);
  }, [onFiles]);

  const onChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    onFiles(e.target.files);
  }, [onFiles]);

  const statusColor = useMemo(() => {
    const s = (lastJob?.status || '').toLowerCase();
    if (s === 'completed') return 'bg-green-100 text-green-800';
    if (s === 'failed') return 'bg-red-100 text-red-800';
    return 'bg-blue-100 text-blue-800';
  }, [lastJob]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
  <h1 className="text-2xl font-semibold text-gray-900 mb-2">Upload Evidence</h1>
  <UploadHelp className="mb-4" />

        <div
          className={`border-2 border-dashed rounded-lg p-10 text-center bg-white ${dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          <p className="text-gray-700 mb-2">Drag & drop files here</p>
          <p className="text-gray-500 text-sm mb-4">PDF, DOCX, XLSX/CSV up to 100MB</p>
          <label className="inline-block px-4 py-2 bg-primary-600 text-white rounded cursor-pointer hover:bg-primary-700">
            {busy ? 'Uploading…' : 'Choose file'}
            <input type="file" className="hidden" onChange={onChange} disabled={busy} />
          </label>
          {error && <div className="text-sm text-red-600 mt-3">{error}</div>}
        </div>

        {lastJob && (
          <div className="bg-white rounded-lg shadow p-4 mt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600">Processing</div>
                <div className="text-gray-900 font-medium">{lastJob.filename || 'Document'}</div>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium ${statusColor}`}>{lastJob.status}</span>
            </div>
            <div className="w-full bg-gray-200 rounded h-2 mt-3">
              <div className="bg-primary-600 h-2 rounded" style={{ width: `${Math.min(100, lastJob.progress || 5)}%` }} />
            </div>
          </div>
        )}

        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Uploads</h2>
          <div className="bg-white rounded-lg shadow divide-y">
            {recent.length === 0 && <div className="p-4 text-sm text-gray-500">No uploads yet.</div>}
            {recent.map((r) => (
              <div key={r.job_id} className="p-4 flex items-center justify-between">
                <div>
                  <div className="text-gray-900">{r.filename}</div>
                  <div className="text-xs text-gray-500">{prettyBytes(r.file_size)} · {new Date(r.updated_at || r.uploaded_at).toLocaleString()}</div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${r.status==='completed'?'bg-green-100 text-green-800':r.status==='failed'?'bg-red-100 text-red-800':'bg-blue-100 text-blue-800'}`}>{r.status}</span>
                  <div className="w-40 bg-gray-200 rounded h-2">
                    <div className="bg-primary-600 h-2 rounded" style={{ width: `${r.progress||0}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
