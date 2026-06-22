interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Loading…" }: LoadingStateProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-surface-border bg-surface-raised px-4 py-6 text-slate-300">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-accent" />
      <span>{label}</span>
    </div>
  );
}
