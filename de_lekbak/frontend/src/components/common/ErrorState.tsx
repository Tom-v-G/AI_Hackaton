interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Something went wrong", message, onRetry }: ErrorStateProps) {
  return (
    <div className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-6">
      <h3 className="text-sm font-semibold text-red-200">{title}</h3>
      <p className="mt-2 text-sm text-red-100/90">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-md bg-red-900/60 px-3 py-2 text-sm font-medium text-red-50 hover:bg-red-900"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
