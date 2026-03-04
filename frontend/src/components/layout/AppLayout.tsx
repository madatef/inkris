import { Outlet } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from './Navbar';
import { Menu } from 'lucide-react';
import { Button } from '../ui/button';

export default function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024);

  useEffect(() => {
    const handleResize = () => {
      setIsDesktop(window.innerWidth >= 1024);
      if (window.innerWidth >= 1024) {
        setNavOpen(true);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-background lg:pt-10 lg:border-box">
      {/* Mobile menu button - only on medium and small screens */}
      {!isDesktop && (
        <Button
          variant="ghost"
          size="icon"
          className="fixed top-4 right-4 z-50"
          onClick={() => setNavOpen(!navOpen)}
        >
          <Menu className="h-5 w-5" />
        </Button>
      )}

      {/* Navbar */}
      <Navbar isOpen={navOpen} isDesktop={isDesktop} onClose={() => setNavOpen(false)} />

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}