import React from 'react';

const UploadHelp: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <h2 className="text-base font-semibold text-gray-900 mb-2">What to upload</h2>
      <p className="text-sm text-gray-700 mb-3">
        Upload institutional documents that demonstrate compliance with your accreditor’s standards: policies,
        handbooks, committee minutes, assessment reports, catalogs, organizational charts, or evidence exports from LMS/SIS.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
        <div>
          <div className="font-medium text-gray-900">Accepted formats</div>
          <div className="text-gray-600">PDF, DOCX, XLSX, CSV, TXT (≤ 100MB each)</div>
        </div>
        <div>
          <div className="font-medium text-gray-900">Tips</div>
          <ul className="list-disc list-inside text-gray-600">
            <li>Prefer final versions over drafts</li>
            <li>Use descriptive filenames</li>
          </ul>
        </div>
        <div>
          <div className="font-medium text-gray-900">After upload</div>
          <div className="text-gray-600">We index documents and surface them in Standards, Reports, and Reviewer Packs.</div>
        </div>
      </div>
    </div>
  );
};

export default UploadHelp;
