import "./App.css";

export default function App() {
  return (
    <main className="app">
      <h1>Forge React Example</h1>
      <p>Deployed with Vite + React via <code>forge deploy</code>.</p>
      <p className="hint">
        Run <code>ping-api</code> separately and call its <code>/ping</code> endpoint
        from Postman — both apps can run at the same time on different ports.
      </p>
    </main>
  );
}
