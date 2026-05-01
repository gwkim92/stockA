"use client";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <section className="panel errorPanel">
      <p className="eyebrow">fixture server unavailable</p>
      <h1>Could not load cockpit data</h1>
      <p className="bodyText">{error.message}</p>
      <button className="button primary" onClick={() => reset()} type="button">
        Retry
      </button>
    </section>
  );
}
