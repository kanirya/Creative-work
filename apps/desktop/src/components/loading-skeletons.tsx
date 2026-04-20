'use client';

type BoxProps = {
  className?: string;
};

function Box({ className = '' }: BoxProps) {
  return <div className={`skeleton-surface ${className}`.trim()} aria-hidden="true" />;
}

export function DashboardSkeleton() {
  return (
    <div className="app-page space-y-6">
      <div className="section-card px-6 py-6">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)]">
          <div className="space-y-4">
            <Box className="h-7 w-28 rounded-full" />
            <Box className="h-11 w-80 max-w-full" />
            <Box className="h-5 w-[32rem] max-w-full" />
            <div className="flex gap-3">
              <Box className="h-8 w-56 rounded-full" />
              <Box className="h-8 w-40 rounded-full" />
            </div>
          </div>
          <Box className="h-36 w-full rounded-[24px]" />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Box key={index} className="h-40 w-full rounded-[24px]" />
        ))}
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.04fr)_minmax(320px,0.96fr)]">
        <Box className="h-[24rem] w-full rounded-[28px]" />
        <Box className="h-[24rem] w-full rounded-[28px]" />
      </div>
    </div>
  );
}

export function CoursesSkeleton() {
  return (
    <div className="app-page space-y-8">
      <div className="space-y-3">
        <Box className="h-10 w-40" />
        <Box className="h-5 w-80 max-w-full" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Box key={index} className="h-52 w-full rounded-[28px]" />
        ))}
      </div>
    </div>
  );
}

export function AssignmentsSkeleton() {
  return (
    <div className="app-page space-y-8">
      <div className="page-header">
        <div className="space-y-3">
          <Box className="h-10 w-48" />
          <Box className="h-5 w-80 max-w-full" />
        </div>
        <Box className="h-20 w-64 rounded-[22px]" />
      </div>
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <Box key={index} className="h-72 w-full rounded-[28px]" />
        ))}
      </div>
    </div>
  );
}

export function GradesSkeleton() {
  return (
    <div className="app-page space-y-8">
      <div className="space-y-3">
        <Box className="h-10 w-36" />
        <Box className="h-5 w-72 max-w-full" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Box key={index} className="h-28 w-full rounded-[28px]" />
        ))}
      </div>
      <Box className="h-80 w-full rounded-[28px]" />
    </div>
  );
}

export function EventsSkeleton() {
  return (
    <div className="app-page space-y-8">
      <div className="space-y-3">
        <Box className="h-10 w-44" />
        <Box className="h-5 w-80 max-w-full" />
      </div>
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <Box key={index} className="h-28 w-full rounded-[28px]" />
        ))}
      </div>
    </div>
  );
}
