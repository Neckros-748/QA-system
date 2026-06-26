import { useState } from "react";
import { NavLink }  from "react-router-dom";
import "./Sidebar.css";


export default function Sidebar() {
	const [open, setOpen] = useState(false);

	const items = [
		{ to: "/documents",   label: "Документы и хранилища", icon: "▤" },
		{ to: "/dialog-tree", label: "Дерево диалога",        icon: "◉" },
		{ to: "/chat",        label: "Чат",                   icon: "✦" },
	];

	return (
		<div
			className={`sidebar-shell ${open ? "sidebar-shell--open" : ""}`}
			onMouseLeave = {() => setOpen(false)}
		>
			{/* Кнопка-триггер */}
			<div
				className="menu-trigger"
				onClick      = {() => setOpen((v) => !v)}
				onMouseEnter = {() => setOpen(true)}
				/* onMouseLeave = {() => setOpen(false)} */
			>
				<span className="menu-trigger__icon">
					{
						open == false ?
						<i className="fas fa-chevron-right"></i> :
						<i className="fas fa-chevron-left"></i>
					}
				</span>
			</div>

			<div
				className="side-menu"
				/* onMouseLeave={() => setOpen(false)} */
			>
				<div className="side-menu__header">
					<div className="side-menu__logo">◎</div>
					<div className="side-menu__title">Конструктор QA-система</div>
				</div>

				<nav className="side-menu__nav">
					{items.map((item) => (
						<NavLink
							key = {item.to}
							to  = {item.to}
							className={({ isActive }) =>
								`side-menu__item ${isActive ? "side-menu__item--active" : ""}`
							}
							onClick={() => setOpen(false)}
						>
							<span className="side-menu__icon">{item.icon}</span>
							<span className="side-menu__label">{item.label}</span>
						</NavLink>
					))}
				</nav>
			</div>
		</div>
	);
}