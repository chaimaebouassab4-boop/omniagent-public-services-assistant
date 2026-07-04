import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { AdminCaseDetailsPage } from "./pages/AdminCaseDetailsPage";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AdminLoginPage } from "./pages/AdminLoginPage";
import { CasesPage } from "./pages/CasesPage";
import { ChatPage } from "./pages/ChatPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { UploadPage } from "./pages/UploadPage";

/** Application route registry for the public services frontend. */
export function App(): JSX.Element {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="chat/:serviceId" element={<ChatPage />} />
        <Route path="upload/:caseId" element={<UploadPage />} />
        <Route path="cases" element={<CasesPage />} />
        <Route path="admin/login" element={<AdminLoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="admin" element={<AdminDashboardPage />} />
          <Route path="admin/case/:id" element={<AdminCaseDetailsPage />} />
        </Route>
        <Route path="admin/case" element={<Navigate to="/admin" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
