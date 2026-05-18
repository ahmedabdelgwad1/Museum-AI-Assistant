export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-gray-100 min-h-screen flex flex-col">
      {/* Main content area */}
      <main className="flex-grow">
        {children}
      </main>
    </div>
  );
}
