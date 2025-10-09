import React, { useEffect, useMemo } from 'react';
import { TourProvider, useTour, type StepType } from '@reactour/tour';

type DashboardTourProps = {
  run: boolean;
  onClose: () => void;
  children: React.ReactNode;
};

const TourController: React.FC<{ run: boolean; onClose: () => void }> = ({ run, onClose }) => {
  const { setIsOpen, isOpen } = useTour();

  useEffect(() => {
    setIsOpen(run);
  }, [run, setIsOpen]);

  useEffect(() => {
    if (!isOpen && run) {
      onClose();
    }
  }, [isOpen, run, onClose]);

  return null;
};

const DashboardTour: React.FC<DashboardTourProps> = ({ run, onClose, children }) => {
  const steps = useMemo<StepType[]>(
    () => [
      {
        selector: '#dashboard-welcome-card',
        content:
          'Start on the welcome card to update your profile, upload evidence, or jump into reviewer workflows.',
      },
      {
        selector: '#dashboard-quick-actions',
        content:
          'Use these quick actions to upload documents, generate reports, and explore standards in one click.',
      },
      {
        selector: '#dashboard-metrics',
        content:
          'This coverage snapshot tracks documents uploaded, standards mapped, compliance score, and checklist coverage.',
      },
      {
        selector: '#dashboard-reviewer-pack',
        content:
          'Build reviewer packs with curated evidence and AI insights tailored for accreditation teams.',
      },
      {
        selector: '#dashboard-insights',
        content:
          'AI insights surface reviewer queue items, readiness scores, and risk hot spots you should monitor.',
      },
      {
        selector: '#dashboard-activity',
        content:
          'Recent activity keeps everyone aligned on the latest uploads, reports, and status changes.',
      },
    ],
    []
  );

  return (
    <TourProvider
      steps={steps}
      scrollSmooth
      showBadge
      showDots
      showNavigation
      showPrevNextButtons
      accessibilityOptions={{
        closeButtonAriaLabel: 'Close guided tour',
        showNavigationScreenReaders: true,
      }}
      beforeClose={() => {
        onClose();
      }}
      onClickMask={() => {
        onClose();
      }}
      onClickClose={() => {
        onClose();
      }}
      styles={{
        popover: () => ({
          borderRadius: 12,
          maxWidth: 360,
          padding: '1rem 1.25rem',
          color: '#1f2937',
          backgroundColor: '#ffffff',
          boxShadow:
            '0 20px 45px rgba(30,64,175,0.15), 0 12px 20px rgba(30,64,175,0.1)',
        }),
        maskWrapper: () => ({
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
        }),
        badge: () => ({
          backgroundColor: '#1e40af',
          color: '#ffffff',
        }),
        controls: () => ({
          color: '#1e40af',
        }),
        button: () => ({
          color: '#1e40af',
        }),
      }}
    >
      <TourController run={run} onClose={onClose} />
      {children}
    </TourProvider>
  );
};

export default DashboardTour;
