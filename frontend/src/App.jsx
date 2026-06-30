import { Navigate, Route, Routes } from "react-router-dom";
import MainLayout from     "./components/Layout/MainLayout";
import DocumentsPage from  "./pages/DocumentsPage/DocumentsPage";
import DialogTreePage from "./pages/DialogTreePage/DialogTreePage";
import ChatPage from       "./pages/ChatPage/ChatPage";

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