import React, { useMemo, useState } from 'react';
import {
  ChevronDownIcon,
  ChevronRightIcon,
  CheckBadgeIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';

interface Responsibility {
  id: string;
  title: string;
  accreditationArea: string;
  owner: string;
  dueDate: string;
  status: 'On Track' | 'Watch' | 'At Risk';
  notes?: string;
}

interface OrgNode {
  id: string;
  name: string;
  leader: string;
  complianceOwner: string;
  coverage: number;
  risk: 'Low' | 'Moderate' | 'High';
  responsibilities: Responsibility[];
  children?: OrgNode[];
}

const responsibilityStatusMeta: Record<Responsibility['status'], { label: string; tone: string; icon: React.FC<{ className?: string }> }> = {
  'On Track': {
    label: 'On Track',
    tone: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    icon: (props) => <CheckBadgeIcon {...props} />, 
  },
  Watch: {
    label: 'Watch',
    tone: 'bg-amber-50 text-amber-700 ring-amber-200',
    icon: (props) => <ClockIcon {...props} />,
  },
  'At Risk': {
    label: 'At Risk',
    tone: 'bg-rose-50 text-rose-700 ring-rose-200',
    icon: (props) => <ExclamationTriangleIcon {...props} />,
  },
};

const initialOrgChart: OrgNode[] = [
  {
    id: 'provost-office',
    name: 'Office of the Provost',
    leader: 'Dr. Elaine Porter',
    complianceOwner: 'Alexis Reed',
    coverage: 86,
    risk: 'Moderate',
    responsibilities: [
      {
        id: 'resp-1',
        title: 'Institutional Effectiveness Narrative',
        accreditationArea: 'SACSCOC 7.1',
        owner: 'Alexis Reed',
        dueDate: '2025-11-15',
        status: 'On Track',
        notes: 'Outline vision alignment with KPIs and upload executive summary.',
      },
      {
        id: 'resp-2',
        title: 'Strategic Planning Evidence Collection',
        accreditationArea: 'SACSCOC 7.3',
        owner: 'Jamie Patel',
        dueDate: '2025-12-01',
        status: 'Watch',
        notes: 'Waiting on institutional research team for updated metrics.',
      },
    ],
    children: [
      {
        id: 'academic-affairs',
        name: 'Academic Affairs',
        leader: 'Dean Marcus Holloway',
        complianceOwner: 'Luis Romero',
        coverage: 78,
        risk: 'High',
        responsibilities: [
          {
            id: 'resp-3',
            title: 'Faculty Credential Audit',
            accreditationArea: 'SACSCOC 6.2.a',
            owner: 'Luis Romero',
            dueDate: '2025-10-30',
            status: 'At Risk',
            notes: 'Pending 12 adjunct files; flagged for escalated support.',
          },
          {
            id: 'resp-4',
            title: 'Curriculum Mapping Refresh',
            accreditationArea: 'SACSCOC 8.2.c',
            owner: 'Priya Desai',
            dueDate: '2025-11-20',
            status: 'Watch',
          },
        ],
        children: [
          {
            id: 'school-business',
            name: 'School of Business',
            leader: 'Assoc. Dean Alana West',
            complianceOwner: 'Robert Lin',
            coverage: 91,
            risk: 'Low',
            responsibilities: [
              {
                id: 'resp-5',
                title: 'Assurance of Learning KPIs',
                accreditationArea: 'AACSB Standard 8',
                owner: 'Robert Lin',
                dueDate: '2025-10-15',
                status: 'On Track',
              },
            ],
          },
          {
            id: 'school-nursing',
            name: 'School of Nursing',
            leader: 'Assoc. Dean Hannah Drake',
            complianceOwner: 'Melissa Grant',
            coverage: 74,
            risk: 'Moderate',
            responsibilities: [
              {
                id: 'resp-6',
                title: 'Clinical Placement Agreements',
                accreditationArea: 'CCNE II-E',
                owner: 'Melissa Grant',
                dueDate: '2025-09-30',
                status: 'Watch',
              },
            ],
          },
        ],
      },
      {
        id: 'student-affairs',
        name: 'Student Affairs & Success',
        leader: 'Vice Provost Tessa Nguyen',
        complianceOwner: 'Jordan Lewis',
        coverage: 88,
        risk: 'Moderate',
        responsibilities: [
          {
            id: 'resp-7',
            title: 'Student Support Services Impact Report',
            accreditationArea: 'SACSCOC 12.1',
            owner: 'Jordan Lewis',
            dueDate: '2025-11-05',
            status: 'On Track',
          },
        ],
      },
    ],
  },
];

interface FlattenedNode {
  id: string;
  name: string;
  path: string;
}

type NewAssignment = {
  nodeId: string;
  title: string;
  accreditationArea: string;
  owner: string;
  dueDate: string;
  notes: string;
};

const OrgChartPage: React.FC = () => {
  const [orgChart, setOrgChart] = useState<OrgNode[]>(initialOrgChart);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ 'provost-office': true, 'academic-affairs': true });
  const [newAssignment, setNewAssignment] = useState<NewAssignment>({
    nodeId: 'academic-affairs',
    title: '',
    accreditationArea: '',
    owner: '',
    dueDate: '',
    notes: '',
  });

  const toggleNode = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const flattenedNodes = useMemo<FlattenedNode[]>(() => {
    const accumulator: FlattenedNode[] = [];

    const traverse = (nodes: OrgNode[], trail: string[]) => {
      nodes.forEach((node) => {
        const nextTrail = [...trail, node.name];
        accumulator.push({ id: node.id, name: node.name, path: nextTrail.join(' › ') });
        if (node.children?.length) {
          traverse(node.children, nextTrail);
        }
      });
    };

    traverse(orgChart, []);
    return accumulator;
  }, [orgChart]);

  const teamMembers = useMemo(() => {
    const members = new Set<string>();
    const collect = (nodes: OrgNode[]) => {
      nodes.forEach((node) => {
        members.add(node.leader);
        members.add(node.complianceOwner);
        node.responsibilities.forEach((resp) => members.add(resp.owner));
        if (node.children?.length) collect(node.children);
      });
    };
    collect(orgChart);
    return Array.from(members).filter(Boolean).sort();
  }, [orgChart]);

  const metrics = useMemo(() => {
    let totalCoverage = 0;
    let nodeCount = 0;
    let totalResponsibilities = 0;
    let atRisk = 0;
    let watch = 0;
    let onTrack = 0;

    const inspect = (nodes: OrgNode[]) => {
      nodes.forEach((node) => {
        totalCoverage += node.coverage;
        nodeCount += 1;
        node.responsibilities.forEach((resp) => {
          totalResponsibilities += 1;
          if (resp.status === 'At Risk') atRisk += 1;
          if (resp.status === 'Watch') watch += 1;
          if (resp.status === 'On Track') onTrack += 1;
        });
        if (node.children?.length) inspect(node.children);
      });
    };

    inspect(orgChart);

    return {
      averageCoverage: nodeCount ? Math.round(totalCoverage / nodeCount) : 0,
      totalResponsibilities,
      atRisk,
      watch,
      onTrack,
    };
  }, [orgChart]);

  const updateResponsibility = (nodeId: string, responsibilityId: string, updates: Partial<Responsibility>) => {
    const applyUpdates = (nodes: OrgNode[]): OrgNode[] =>
      nodes.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            responsibilities: node.responsibilities.map((resp) =>
              resp.id === responsibilityId ? { ...resp, ...updates } : resp
            ),
          };
        }
        if (node.children?.length) {
          return { ...node, children: applyUpdates(node.children) };
        }
        return node;
      });

    setOrgChart((prev) => applyUpdates(prev));
  };

  const handleAddResponsibility = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newAssignment.title.trim() || !newAssignment.nodeId) return;

    const createWithNode = (nodes: OrgNode[]): OrgNode[] =>
      nodes.map((node) => {
        if (node.id === newAssignment.nodeId) {
          const created: Responsibility = {
            id: `resp-${Date.now()}`,
            title: newAssignment.title.trim(),
            accreditationArea: newAssignment.accreditationArea.trim() || 'General Compliance',
            owner: newAssignment.owner || node.complianceOwner,
            dueDate: newAssignment.dueDate || new Date().toISOString().slice(0, 10),
            status: 'Watch',
            notes: newAssignment.notes.trim() || undefined,
          };
          return { ...node, responsibilities: [...node.responsibilities, created] };
        }
        if (node.children?.length) {
          return { ...node, children: createWithNode(node.children) };
        }
        return node;
      });

    setOrgChart((prev) => createWithNode(prev));
    setExpanded((prev) => ({ ...prev, [newAssignment.nodeId]: true }));
    setNewAssignment((prev) => ({ ...prev, title: '', accreditationArea: '', notes: '' }));
  };

  const cycleStatus = (status: Responsibility['status']): Responsibility['status'] => {
    if (status === 'On Track') return 'Watch';
    if (status === 'Watch') return 'At Risk';
    return 'On Track';
  };

  const renderOrgNodes = (nodes: OrgNode[], depth = 0) => (
    <div className={`${depth > 0 ? 'border-l border-dashed border-gray-200 pl-6 md:pl-8' : ''} space-y-4`}> 
      {nodes.map((node) => {
        const isExpanded = expanded[node.id] ?? depth < 1;
        return (
          <div key={node.id} className="space-y-4">
            <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
              <div className="flex flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-start gap-3">
                  <button
                    type="button"
                    onClick={() => toggleNode(node.id)}
                    className="mt-1 rounded-full border border-gray-200 p-1 text-gray-500 hover:bg-gray-50"
                    aria-label={isExpanded ? 'Collapse' : 'Expand'}
                  >
                    {isExpanded ? <ChevronDownIcon className="h-4 w-4" /> : <ChevronRightIcon className="h-4 w-4" />}
                  </button>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{node.name}</h3>
                    <p className="text-sm text-gray-600">
                      Lead: <span className="font-medium">{node.leader}</span> · Compliance owner:{' '}
                      <span className="font-medium text-primary-700">{node.complianceOwner}</span>
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="inline-flex items-center rounded-full bg-primary-50 px-3 py-1 font-medium text-primary-700">
                        Coverage: {node.coverage}%
                      </span>
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1 font-medium ${
                          node.risk === 'High'
                            ? 'bg-rose-50 text-rose-700'
                            : node.risk === 'Moderate'
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-emerald-50 text-emerald-700'
                        }`}
                      >
                        Risk: {node.risk}
                      </span>
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 font-medium text-gray-600">
                        {node.responsibilities.length} assignments
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col gap-2 md:text-right">
                  <p className="text-sm text-gray-500">Accountable team</p>
                  <p className="text-sm font-medium text-gray-900">
                    {Array.from(
                      new Set([
                        node.leader,
                        node.complianceOwner,
                        ...node.responsibilities.map((resp) => resp.owner),
                      ])
                    )
                      .filter(Boolean)
                      .join(', ')}
                  </p>
                </div>
              </div>
              {isExpanded && (
                <div className="border-t border-gray-100 px-5 py-4">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600">Responsibility</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600">Accreditation Area</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600">Owner</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600">Due</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600">Status</th>
                          <th className="px-3 py-2 text-left font-semibold text-gray-600">Notes</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {node.responsibilities.map((resp) => {
                          const statusMeta = responsibilityStatusMeta[resp.status];
                          const StatusIcon = statusMeta.icon;
                          return (
                            <tr key={resp.id} className="align-top">
                              <td className="px-3 py-3">
                                <p className="font-medium text-gray-900">{resp.title}</p>
                              </td>
                              <td className="px-3 py-3 text-gray-600">{resp.accreditationArea}</td>
                              <td className="px-3 py-3">
                                <input
                                  value={resp.owner}
                                  onChange={(event) =>
                                    updateResponsibility(node.id, resp.id, { owner: event.target.value })
                                  }
                                  className="w-full rounded-md border border-gray-200 px-2 py-1 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                                />
                              </td>
                              <td className="px-3 py-3 text-gray-600">
                                <input
                                  type="date"
                                  value={resp.dueDate}
                                  onChange={(event) =>
                                    updateResponsibility(node.id, resp.id, { dueDate: event.target.value })
                                  }
                                  className="rounded-md border border-gray-200 px-2 py-1 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                                />
                              </td>
                              <td className="px-3 py-3">
                                <button
                                  type="button"
                                  onClick={() =>
                                    updateResponsibility(node.id, resp.id, { status: cycleStatus(resp.status) })
                                  }
                                  className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset transition ${statusMeta.tone}`}
                                >
                                  <StatusIcon className="h-4 w-4" />
                                  {statusMeta.label}
                                </button>
                              </td>
                              <td className="px-3 py-3 text-gray-600">
                                <textarea
                                  value={resp.notes || ''}
                                  onChange={(event) =>
                                    updateResponsibility(node.id, resp.id, { notes: event.target.value })
                                  }
                                  rows={2}
                                  className="w-full rounded-md border border-gray-200 px-2 py-1 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                                />
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
            {isExpanded && node.children?.length ? (
              <div className="pl-4 md:pl-6">
                {renderOrgNodes(node.children, depth + 1)}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-gray-200 bg-gradient-to-br from-white via-white to-primary-50/60 p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl">
            <h1 className="text-3xl font-semibold text-gray-900">Dynamic Org Chart & Accountability Map</h1>
            <p className="mt-3 text-sm leading-6 text-gray-600">
              Visualize compliance ownership across academic and administrative units, assign deliverables, and track real-time status. The org chart below stays in lockstep with accreditation responsibilities so every finding has an accountable owner and due date.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-xl border border-primary-100 bg-white p-4 text-primary-900 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-primary-500">Avg. Coverage</p>
              <p className="mt-1 text-2xl font-semibold">{metrics.averageCoverage}%</p>
              <p className="text-xs text-primary-700">Weighted across all units</p>
            </div>
            <div className="rounded-xl border border-emerald-100 bg-emerald-50/80 p-4 text-emerald-900 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-emerald-600">Assignments On Track</p>
              <p className="mt-1 text-2xl font-semibold">{metrics.onTrack}</p>
              <p className="text-xs text-emerald-700">of {metrics.totalResponsibilities} responsibilities</p>
            </div>
            <div className="rounded-xl border border-amber-100 bg-amber-50/70 p-4 text-amber-900 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-amber-600">Watch Items</p>
              <p className="mt-1 text-2xl font-semibold">{metrics.watch}</p>
              <p className="text-xs text-amber-700">Require weekly check-ins</p>
            </div>
            <div className="rounded-xl border border-rose-100 bg-rose-50/70 p-4 text-rose-900 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-rose-600">At Risk</p>
              <p className="mt-1 text-2xl font-semibold">{metrics.atRisk}</p>
              <p className="text-xs text-rose-700">Escalated to leadership</p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-6">
        <div className="flex flex-col gap-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900">Add or Reassign Compliance Work</h2>
          <form onSubmit={handleAddResponsibility} className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="text-gray-600">Org unit</span>
              <select
                value={newAssignment.nodeId}
                onChange={(event) => setNewAssignment((prev) => ({ ...prev, nodeId: event.target.value }))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              >
                {flattenedNodes.map((node) => (
                  <option key={node.id} value={node.id}>
                    {node.path}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm">
              <span className="text-gray-600">Assignment title</span>
              <input
                required
                value={newAssignment.title}
                onChange={(event) => setNewAssignment((prev) => ({ ...prev, title: event.target.value }))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                placeholder="e.g., Annual program assessment audit"
              />
            </label>

            <label className="text-sm">
              <span className="text-gray-600">Accreditation focus</span>
              <input
                value={newAssignment.accreditationArea}
                onChange={(event) => setNewAssignment((prev) => ({ ...prev, accreditationArea: event.target.value }))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                placeholder="SACSCOC 8.2.b"
              />
            </label>

            <label className="text-sm">
              <span className="text-gray-600">Primary owner</span>
              <input
                value={newAssignment.owner}
                onChange={(event) => setNewAssignment((prev) => ({ ...prev, owner: event.target.value }))}
                list="org-team-members"
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                placeholder="Assign to team member"
              />
              <datalist id="org-team-members">
                {teamMembers.map((member) => (
                  <option key={member} value={member} />
                ))}
              </datalist>
            </label>

            <label className="text-sm">
              <span className="text-gray-600">Due date</span>
              <input
                type="date"
                value={newAssignment.dueDate}
                onChange={(event) => setNewAssignment((prev) => ({ ...prev, dueDate: event.target.value }))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>

            <label className="md:col-span-2 text-sm">
              <span className="text-gray-600">Context / notes</span>
              <textarea
                value={newAssignment.notes}
                onChange={(event) => setNewAssignment((prev) => ({ ...prev, notes: event.target.value }))}
                rows={3}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                placeholder="Add context for reviewers or link to supporting evidence"
              />
            </label>

            <div className="md:col-span-2 flex items-center justify-between border-t border-dashed border-gray-200 pt-4">
              <p className="text-xs text-gray-500">
                Each assignment appears instantly in the unit dashboard and reviewer pack exports.
              </p>
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-700"
              >
                <PlusIcon className="h-4 w-4" />
                Add responsibility
              </button>
            </div>
          </form>
        </div>

        {renderOrgNodes(orgChart)}
      </section>
    </div>
  );
};

export default OrgChartPage;
