import React, { useMemo, useState } from 'react';
import {
  ArrowTrendingUpIcon,
  BanknotesIcon,
  ChartPieIcon,
  ClipboardDocumentCheckIcon,
  ClockIcon,
  DocumentChartBarIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';

interface ScenarioInputs {
  currentHoursPerMonth: number;
  hourlyCost: number;
  accreditationCyclesPerYear: number;
  baselineFindingsPerCycle: number;
  avgPenaltyPerFinding: number;
  automationAdoption: number; // percentage 0-100
  reviewTimeReduction: number; // percentage 0-100
  coverageLift: number; // percentage 0-100
  platformInvestment: number; // annual cost
  trainingInvestment: number; // one-time cost amortized
}

interface ScenarioResult {
  timeSavingsValue: number;
  hoursSaved: number;
  riskAvoidance: number;
  totalBenefits: number;
  roi: number;
  breakEvenMonths: number;
}

interface SavedScenario {
  id: string;
  name: string;
  inputs: ScenarioInputs;
  results: ScenarioResult;
}

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

const defaultInputs: ScenarioInputs = {
  currentHoursPerMonth: 240,
  hourlyCost: 58,
  accreditationCyclesPerYear: 2,
  baselineFindingsPerCycle: 6,
  avgPenaltyPerFinding: 12000,
  automationAdoption: 65,
  reviewTimeReduction: 45,
  coverageLift: 30,
  platformInvestment: 48000,
  trainingInvestment: 8000,
};

const ScenarioModelingPage: React.FC = () => {
  const [inputs, setInputs] = useState<ScenarioInputs>(defaultInputs);
  const [scenarioName, setScenarioName] = useState('FY26 Accreditation Plan');
  const [saved, setSaved] = useState<SavedScenario[]>([]);

  const results = useMemo<ScenarioResult>(() => {
    const adoptionFactor = inputs.automationAdoption / 100;
    const timeReductionFactor = inputs.reviewTimeReduction / 100;

    const baselineAnnualHours = inputs.currentHoursPerMonth * 12;
    const hoursSaved = baselineAnnualHours * adoptionFactor * timeReductionFactor;
    const timeSavingsValue = hoursSaved * inputs.hourlyCost;

    const coverageImprovement = inputs.coverageLift / 100;
    const avoidedFindings =
      inputs.baselineFindingsPerCycle * inputs.accreditationCyclesPerYear * coverageImprovement * adoptionFactor;
    const riskAvoidance = avoidedFindings * inputs.avgPenaltyPerFinding;

    const amortizedTraining = inputs.trainingInvestment / 3; // amortize onboarding over 3 years
    const totalInvestment = inputs.platformInvestment + amortizedTraining;

    const totalBenefits = timeSavingsValue + riskAvoidance;
    const roi = totalInvestment ? ((totalBenefits - totalInvestment) / totalInvestment) * 100 : 0;
    const monthlyBenefits = totalBenefits / 12;
    const breakEvenMonths = monthlyBenefits > 0 ? Math.max(0, Math.round(totalInvestment / monthlyBenefits)) : Infinity;

    return {
      timeSavingsValue,
      hoursSaved,
      riskAvoidance,
      totalBenefits,
      roi,
      breakEvenMonths,
    };
  }, [inputs]);

  const adoptionSensitivity = useMemo(() => {
    const adoptionLevels = [40, 60, 80, 100];
    return adoptionLevels.map((level) => {
      const adoptionFactor = level / 100;
      const timeReductionFactor = inputs.reviewTimeReduction / 100;
      const baselineAnnualHours = inputs.currentHoursPerMonth * 12;
      const hoursSaved = baselineAnnualHours * adoptionFactor * timeReductionFactor;
      const timeSavingsValue = hoursSaved * inputs.hourlyCost;

      const coverageImprovement = inputs.coverageLift / 100;
      const avoidedFindings =
        inputs.baselineFindingsPerCycle * inputs.accreditationCyclesPerYear * coverageImprovement * adoptionFactor;
      const riskAvoidance = avoidedFindings * inputs.avgPenaltyPerFinding;

      const amortizedTraining = inputs.trainingInvestment / 3;
      const totalInvestment = inputs.platformInvestment + amortizedTraining;
      const totalBenefits = timeSavingsValue + riskAvoidance;
      const roi = totalInvestment ? ((totalBenefits - totalInvestment) / totalInvestment) * 100 : 0;

      return { level, roi, timeSavingsValue, riskAvoidance };
    });
  }, [inputs]);

  const handleInputChange = (field: keyof ScenarioInputs, value: number) => {
    setInputs((prev) => ({ ...prev, [field]: Number.isFinite(value) ? value : prev[field] }));
  };

  const handleSaveScenario = () => {
    const trimmedName = scenarioName.trim() || `Scenario ${saved.length + 1}`;
    const newScenario: SavedScenario = {
      id: `scenario-${Date.now()}`,
      name: trimmedName,
      inputs,
      results,
    };
    setSaved((prev) => [newScenario, ...prev]);
  };

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-gray-200 bg-gradient-to-br from-white via-white to-emerald-50 p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl">
            <h1 className="text-3xl font-semibold text-gray-900">Scenario Modeling & ROI Calculator</h1>
            <p className="mt-3 text-sm leading-6 text-gray-600">
              Quantify the financial and operational impact of A³E. Adjust adoption levels, time savings, and compliance lift to see how accreditation automation reduces cost while mitigating risk exposure.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-xl border border-emerald-100 bg-white p-4 text-emerald-900 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-emerald-600">Annual net benefit</p>
              <p className="mt-1 text-2xl font-semibold">{currency.format(results.totalBenefits)}</p>
              <p className="text-xs text-emerald-700">Time + risk avoidance</p>
            </div>
            <div className="rounded-xl border border-primary-100 bg-white p-4 text-primary-900 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-primary-500">ROI</p>
              <p className="mt-1 text-2xl font-semibold">{results.roi.toFixed(1)}%</p>
              <p className="text-xs text-primary-700">After platform + training investment</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3 space-y-5 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900">Operational Inputs</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="text-gray-600">Current hours spent monthly</span>
              <input
                type="number"
                min={0}
                value={inputs.currentHoursPerMonth}
                onChange={(event) => handleInputChange('currentHoursPerMonth', Number(event.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>
            <label className="text-sm">
              <span className="text-gray-600">Weighted hourly cost ($)</span>
              <input
                type="number"
                min={0}
                value={inputs.hourlyCost}
                onChange={(event) => handleInputChange('hourlyCost', Number(event.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>
            <label className="text-sm">
              <span className="text-gray-600">Accreditation cycles / year</span>
              <input
                type="number"
                min={1}
                value={inputs.accreditationCyclesPerYear}
                onChange={(event) => handleInputChange('accreditationCyclesPerYear', Number(event.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>
            <label className="text-sm">
              <span className="text-gray-600">Findings per cycle (baseline)</span>
              <input
                type="number"
                min={0}
                value={inputs.baselineFindingsPerCycle}
                onChange={(event) => handleInputChange('baselineFindingsPerCycle', Number(event.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>
            <label className="text-sm">
              <span className="text-gray-600">Avg. cost per finding ($)</span>
              <input
                type="number"
                min={0}
                value={inputs.avgPenaltyPerFinding}
                onChange={(event) => handleInputChange('avgPenaltyPerFinding', Number(event.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>
            <label className="text-sm">
              <span className="text-gray-600">Platform investment (annual $)</span>
              <input
                type="number"
                min={0}
                value={inputs.platformInvestment}
                onChange={(event) => handleInputChange('platformInvestment', Number(event.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>
            <label className="text-sm">
              <span className="text-gray-600">Training & change mgmt (one-time $)</span>
              <input
                type="number"
                min={0}
                value={inputs.trainingInvestment}
                onChange={(event) => handleInputChange('trainingInvestment', Number(event.target.value))}
                className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
            </label>
          </div>

          <div className="grid gap-6 rounded-xl border border-dashed border-gray-200 bg-gray-50 p-4 md:grid-cols-3">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Automation adoption</label>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{inputs.automationAdoption}%</p>
              <input
                type="range"
                min={10}
                max={100}
                step={5}
                value={inputs.automationAdoption}
                onChange={(event) => handleInputChange('automationAdoption', Number(event.target.value))}
                className="mt-3 w-full"
              />
              <p className="mt-1 text-xs text-gray-500">Percent of workflows using A³E automation</p>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Review time reduction</label>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{inputs.reviewTimeReduction}%</p>
              <input
                type="range"
                min={10}
                max={70}
                step={5}
                value={inputs.reviewTimeReduction}
                onChange={(event) => handleInputChange('reviewTimeReduction', Number(event.target.value))}
                className="mt-3 w-full"
              />
              <p className="mt-1 text-xs text-gray-500">Average percentage reduction in manual review time</p>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Coverage improvement</label>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{inputs.coverageLift}%</p>
              <input
                type="range"
                min={5}
                max={60}
                step={5}
                value={inputs.coverageLift}
                onChange={(event) => handleInputChange('coverageLift', Number(event.target.value))}
                className="mt-3 w-full"
              />
              <p className="mt-1 text-xs text-gray-500">Lift in evidence coverage vs. baseline year</p>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-5">
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-gray-900">Modeled Outcomes</h2>
            <dl className="mt-6 space-y-4">
              <div className="flex items-center justify-between rounded-lg bg-emerald-50/60 px-4 py-3">
                <dt className="flex items-center gap-2 text-sm font-medium text-emerald-900">
                  <ClockIcon className="h-5 w-5" />
                  Hours saved annually
                </dt>
                <dd className="text-lg font-semibold text-emerald-900">{Math.round(results.hoursSaved).toLocaleString()}</dd>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-primary-50/60 px-4 py-3">
                <dt className="flex items-center gap-2 text-sm font-medium text-primary-900">
                  <BanknotesIcon className="h-5 w-5" />
                  Time savings value (annual)
                </dt>
                <dd className="text-lg font-semibold text-primary-900">{currency.format(results.timeSavingsValue)}</dd>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-amber-50/70 px-4 py-3">
                <dt className="flex items-center gap-2 text-sm font-medium text-amber-900">
                  <DocumentChartBarIcon className="h-5 w-5" />
                  Risk avoidance from fewer findings
                </dt>
                <dd className="text-lg font-semibold text-amber-900">{currency.format(results.riskAvoidance)}</dd>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-rose-50/70 px-4 py-3">
                <dt className="flex items-center gap-2 text-sm font-medium text-rose-900">
                  <ClipboardDocumentCheckIcon className="h-5 w-5" />
                  Break-even timeline (months)
                </dt>
                <dd className="text-lg font-semibold text-rose-900">
                  {Number.isFinite(results.breakEvenMonths) ? results.breakEvenMonths : 'N/A'}
                </dd>
              </div>
            </dl>
            <div className="mt-6 border-t border-dashed border-gray-200 pt-4 text-xs text-gray-500">
              ROI calculations amortize training over three years. Adjust the platform investment to match your contracted subscription tier.
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Save Scenario</h2>
            <div className="mt-4 space-y-3">
              <label className="text-sm text-gray-600">
                Scenario name
                <input
                  value={scenarioName}
                  onChange={(event) => setScenarioName(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  placeholder="e.g., Board presentation Q4"
                />
              </label>
              <button
                type="button"
                onClick={handleSaveScenario}
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-700"
              >
                <PlusIcon className="h-4 w-4" /> Save scenario snapshot
              </button>
            </div>
            {saved.length > 0 && (
              <div className="mt-5 space-y-3">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Saved comparisons</h3>
                <ul className="space-y-2 text-sm">
                  {saved.map((scenario) => (
                    <li key={scenario.id} className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
                      <div>
                        <p className="font-medium text-gray-900">{scenario.name}</p>
                        <p className="text-xs text-gray-500">ROI {scenario.results.roi.toFixed(1)}% • Benefits {currency.format(scenario.results.totalBenefits)}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setInputs(scenario.inputs);
                          setScenarioName(`${scenario.name} (edited)`);
                        }}
                        className="text-xs font-semibold text-primary-600 hover:text-primary-700"
                      >
                        Load inputs
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Adoption & Coverage Sensitivity</h2>
            <p className="text-sm text-gray-600">Model upside at increasing automation adoption levels while holding other variables constant.</p>
          </div>
          <div className="flex gap-3 text-xs">
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 font-medium text-emerald-700">
              <ArrowTrendingUpIcon className="h-4 w-4" /> ROI trajectory
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1 font-medium text-amber-700">
              <ChartPieIcon className="h-4 w-4" /> Risk avoidance
            </span>
          </div>
        </div>

        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-semibold text-gray-600">Automation adoption</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-600">ROI</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-600">Time savings</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-600">Risk avoidance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {adoptionSensitivity.map((row) => (
                <tr key={row.level}>
                  <td className="px-4 py-3 font-medium text-gray-900">{row.level}%</td>
                  <td className="px-4 py-3 text-primary-700">{row.roi.toFixed(1)}%</td>
                  <td className="px-4 py-3 text-gray-600">{currency.format(row.timeSavingsValue)}</td>
                  <td className="px-4 py-3 text-amber-700">{currency.format(row.riskAvoidance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm">
            <p className="font-semibold text-gray-900">Board-ready summary</p>
            <p className="mt-2 text-gray-600">
              Export saved scenarios to communicate strategic upside, project break-even timelines, and align executive sponsors on staffing assumptions.
            </p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm">
            <p className="font-semibold text-gray-900">Fine-tune adoption roadmap</p>
            <p className="mt-2 text-gray-600">
              Sensitivity table highlights where change management accelerates ROI. Pair with our implementation playbook for a phased rollout.
            </p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm">
            <p className="font-semibold text-gray-900">Audit defensibility</p>
            <p className="mt-2 text-gray-600">
              Automatically factor in risk reduction from fewer deficiencies and use outputs to budget for accreditation reserves.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ScenarioModelingPage;
