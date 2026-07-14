import AppRouter from "@/routes/AppRouter";

function App() {
  console.log(import.meta.env.VITE_API_BASE_URL);
  return (
    <div>
      <AppRouter />
    </div>
  );
}

export default App;