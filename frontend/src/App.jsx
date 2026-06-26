import { Navigate, Route, Routes } from "react-router-dom";
import MainLayout from     "./components/Layout/MainLayout";
import DialogTreePage from "./pages/DialogTreePage";
import DocumentsPage from  "./pages/DocumentsPage/DocumentsPage";
import ChatPage from       "./pages/ChatPage";

export default function App() {
	return (
		<Routes>
			<Route element={<MainLayout />}>
				<Route path="/" element={<Navigate to="/documents" replace />} />
				<Route path="/documents" element={<DocumentsPage />} />
				<Route path="/dialog-tree" element={<DialogTreePage />} />
				<Route path="/chat" element={<ChatPage />} />
			</Route>
		</Routes>
	);
}