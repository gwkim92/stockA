import Link from "next/link";

export default function NotFound() {
  return (
    <section className="panel errorPanel">
      <p className="eyebrow">route not mapped</p>
      <h1>This cockpit route does not exist yet.</h1>
      <Link className="button primary" href="/">
        Return to cockpit
      </Link>
    </section>
  );
}
