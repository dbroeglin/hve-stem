import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { AppHeader } from "./components/AppHeader";
import { AssessPage } from "./pages/AssessPage";
import { RemediatePage } from "./pages/RemediatePage";

export default function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <AppHeader />
        <div className="app-container">
          <Routes>
            <Route path="/assess" element={<AssessPage />} />
            <Route path="/remediate" element={<RemediatePage />} />
            <Route path="*" element={<Navigate to="/assess" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
