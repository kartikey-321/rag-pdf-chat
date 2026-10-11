import { NavLink } from "react-router-dom";

export default function Sidebar() {
  const links = [
    { label: "Documents", path: "/documents" },
    { label: "Chat", path: "/chat" },
  ];

  return (
    <aside className="min-h-screen w-60 border-r border-slate-200 bg-slate-50 p-4">
      <h1 className="mb-10 text-xl font-bold text-blue-600">
        PDF AI Chat
      </h1>

      <nav className="space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.path}
            to={link.path}
            className={({ isActive }) =>
              `block rounded-lg px-4 py-3 ${
                isActive
                  ? "bg-blue-100 text-blue-700"
                  : "text-slate-600 hover:bg-slate-100"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}