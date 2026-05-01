export default function Loading() {
  return (
    <div className="pageStack">
      <section className="panel loadingPanel" aria-busy="true">
        <p className="eyebrow">loading fixture read model</p>
        <h1>Preparing cockpit snapshot</h1>
      </section>
    </div>
  );
}
