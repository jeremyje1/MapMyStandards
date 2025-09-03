export default function ErrorPage({ searchParams }) {
  const code = searchParams?.error;
  return (
    <main className="p-8 max-w-md mx-auto">
      <h1 className="text-xl font-semibold mb-4">Authentication Error</h1>
      {code && <p className="text-red-600">Code: {code}</p>}
      <p>Please retry. If the issue persists contact support.</p>
    </main>
  );
}