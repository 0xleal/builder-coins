export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black/20 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-white/60">
          <p>
            &copy;{new Date().getFullYear()} BuildersFund. Building the future
            of decentralized finance.
          </p>
        </div>
      </div>
    </footer>
  );
}
