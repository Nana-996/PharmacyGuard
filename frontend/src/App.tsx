import { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginView } from './views/LoginView';
import { Sidebar } from './components/layout/Sidebar';
import type { NavView } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardView } from './views/DashboardView';
import { PrescriptionReviewView } from './views/PrescriptionReviewView';
import { NewPrescriptionView } from './views/NewPrescriptionView';
import { ReviewQueueView } from './views/ReviewQueueView';
import { InventoryView } from './views/InventoryView';
import { ChiefPharmacistView } from './views/ChiefPharmacistView';
import { CaseDetailsView } from './views/CaseDetailsView';
import { StudentWorkspaceView } from './views/StudentWorkspaceView';
import { api } from './services/api';
import { Activity } from 'lucide-react';


function AuthenticatedApp() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [activeView, setActiveView] = useState<NavView>(user?.role === 'PHARMACY_STUDENT' ? 'student' : 'dashboard');
  const [targetRxId, setTargetRxId] = useState<string>('RX-1003');
  const [targetReviewId, setTargetReviewId] = useState<string | undefined>(undefined);

  // Real badge counts for sidebar
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [lowStockCount, setLowStockCount] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshBadges = useCallback(async () => {
    if (!isAuthenticated || user?.role === 'PHARMACY_STUDENT') return;
    setIsRefreshing(true);
    try {
      const [pendingRes, lowRes] = await Promise.all([
        api.getPendingReviews().catch(() => ({ total_pending: 0 })),
        api.getLowStockItems().catch(() => ({ total_low_stock_items: 0 })),
      ]);
      setPendingCount(pendingRes.total_pending || 0);
      setLowStockCount(lowRes.total_low_stock_items || 0);
    } catch {
      // Non-critical badge count update
    } finally {
      setIsRefreshing(false);
    }
  }, [isAuthenticated, user?.role]);

  useEffect(() => {
    refreshBadges();
  }, [refreshBadges, activeView]);

  // Reset view to designated role landing page whenever user logs in or switches roles
  useEffect(() => {
    if (!user) {
      setActiveView('dashboard');
      setTargetReviewId(undefined);
      return;
    }
    if (user.role === 'PHARMACY_STUDENT') {
      setActiveView('student');
    } else {
      setActiveView('dashboard');
    }
    setTargetReviewId(undefined);
  }, [user?.user_id, user?.role]);



  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--pg-bg)] flex flex-col items-center justify-center space-y-4">
        <div className="w-11 h-11 rounded-xl bg-blue-600 flex items-center justify-center shadow-sm">
          <Activity className="w-6 h-6 text-white animate-pulse" />
        </div>
        <div className="text-center">
          <div className="text-sm font-semibold text-[var(--pg-text)]">Loading PharmacyGuard...</div>
          <div className="text-xs text-[var(--pg-text-muted)] mt-1">Verifying session</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  // Handlers for seamless cross-view navigation
  const handleStartReview = (rxId: string) => {
    setTargetRxId(rxId);
    setTargetReviewId(undefined);
    setActiveView('review');
  };

  const handleOpenReview = (reviewId: string) => {
    setTargetReviewId(reviewId);
    setActiveView('review');
  };

  const handleOpenCaseDetails = (reviewId: string) => {
    setTargetReviewId(reviewId);
    setActiveView('case_details');
  };

  const handlePrescriptionCreated = (rxId: string, reviewId?: string) => {
    setTargetRxId(rxId);
    setTargetReviewId(reviewId);
    setActiveView('review');
    refreshBadges();
  };

  return (
    <div className="flex min-h-screen bg-[var(--pg-bg)] text-[var(--pg-text)] font-sans antialiased selection:bg-blue-100 selection:text-blue-900">
      {/* Persistent Navigation Sidebar */}
      <Sidebar
        activeView={activeView}
        onNavigate={(view) => {
          // Route guard: restrict Chief view to CHIEF_PHARMACIST
          if (view === 'analytics' && user?.role !== 'CHIEF_PHARMACIST') {
            return;
          }
          // Route guard: restrict clinical views from student
          if (user?.role === 'PHARMACY_STUDENT' && view !== 'student') {
            return;
          }
          setActiveView(view);
          if (view !== 'review') setTargetReviewId(undefined);
        }}
        pendingCount={pendingCount}
        lowStockCount={lowStockCount}
      />

      {/* Main App Layout */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen overflow-hidden">
        <Header onRefresh={refreshBadges} isRefreshing={isRefreshing} />

        <main className="flex-1 p-5 lg:p-7 overflow-y-auto max-w-7xl w-full mx-auto">
          {/* Student Educational Training Lab View */}
          {activeView === 'student' && <StudentWorkspaceView />}


          {activeView === 'dashboard' && user?.role !== 'PHARMACY_STUDENT' && (
            <DashboardView
              onStartReview={handleStartReview}
              onOpenReview={handleOpenReview}
              onOpenCaseDetails={handleOpenCaseDetails}
              onNavigateToQueue={() => setActiveView(user?.role === 'ADMIN' ? 'inventory' : 'queue')}
              onNavigateToInventory={() => setActiveView('inventory')}
            />
          )}

          {activeView === 'new_prescription' && user?.role !== 'PHARMACY_STUDENT' && (
            <NewPrescriptionView
              onPrescriptionCreated={handlePrescriptionCreated}
              onCancel={() => setActiveView('queue')}
            />
          )}

          {activeView === 'review' && user?.role !== 'PHARMACY_STUDENT' && (
            <PrescriptionReviewView
              initialRxId={targetRxId}
              initialReviewId={targetReviewId}
              onNavigateToCaseDetails={handleOpenCaseDetails}
              onBackToDashboard={() => setActiveView('dashboard')}
            />
          )}

          {activeView === 'queue' && user?.role !== 'PHARMACY_STUDENT' && (
            <ReviewQueueView
              onOpenReview={handleOpenReview}
              onOpenCaseDetails={handleOpenCaseDetails}
              onNewReview={() => setActiveView('new_prescription')}
            />
          )}

          {activeView === 'inventory' && user?.role !== 'PHARMACY_STUDENT' && <InventoryView />}

          {activeView === 'analytics' && user?.role === 'CHIEF_PHARMACIST' && (
            <ChiefPharmacistView
              onOpenCaseDetails={handleOpenCaseDetails}
              onOpenReview={handleOpenReview}
            />
          )}

          {activeView === 'case_details' && user?.role !== 'PHARMACY_STUDENT' && (
            <CaseDetailsView
              initialReviewId={targetReviewId}
              onOpenReview={handleOpenReview}
              onBack={() => setActiveView('dashboard')}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}

export default App;
