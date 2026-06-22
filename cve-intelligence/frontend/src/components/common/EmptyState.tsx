interface EmptyStateProps {
  title: string;
  description?: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-surface-border bg-surface-raised/40 px-4 py-8 text-center">
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      {description ? <p className="mt-2 text-sm text-slate-400">{description}</p> : null}
    </div>
  );
}
