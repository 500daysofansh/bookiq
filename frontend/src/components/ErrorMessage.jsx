export default function ErrorMessage({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <div className="text-5xl">⚠️</div>
      <p className="text-red-400 text-lg font-medium">Something went wrong</p>
      <p className="text-slate-500 text-sm max-w-md">{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
