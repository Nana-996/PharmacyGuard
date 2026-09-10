import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, AlertCircle, LogIn, ArrowRight, Check } from 'lucide-react';
import { Logo } from '../components/common/Logo';

export const LoginView: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [activeLoginRole, setActiveLoginRole] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectAccount = (devEmail: string, devPass: string, role: string) => {
    setEmail(devEmail);
    setPassword(devPass);
    setSelectedRole(role);
    setError(null);
  };

  const handleDirectSignIn = async (devEmail: string, devPass: string, role: string) => {
    setEmail(devEmail);
    setPassword(devPass);
    setSelectedRole(role);
    setError(null);
    setIsSubmitting(true);
    setActiveLoginRole(role);
    try {
      await login({ email: devEmail.trim(), password: devPass });
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
      setActiveLoginRole(null);
    }
  };

  const testAccounts = [
    {
      label: 'Staff Pharmacist',
      name: 'Dr. Alex Reed, PharmD',
      email: 'staff.pharmacist@hospital.dev',
      pass: 'DevStaff123!',
      role: 'STAFF_PHARMACIST',
      badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
      activeBorder: 'border-blue-500 ring-2 ring-blue-100 bg-blue-50/40'
    },
    {
      label: 'Chief Pharmacist',
      name: 'Dr. Eleanor Vance, PharmD',
      email: 'chief.pharmacist@hospital.dev',
      pass: 'DevChief123!',
      role: 'CHIEF_PHARMACIST',
      badgeColor: 'bg-violet-100 text-violet-800 border-violet-200',
      activeBorder: 'border-violet-500 ring-2 ring-violet-100 bg-violet-50/40'
    },
    {
      label: 'Pharmacy Student',
      name: 'Sam Taylor (Intern)',
      email: 'student@hospital.dev',
      pass: 'DevStudent123!',
      role: 'PHARMACY_STUDENT',
      badgeColor: 'bg-sky-100 text-sky-800 border-sky-200',
      activeBorder: 'border-sky-500 ring-2 ring-sky-100 bg-sky-50/40'
    },
    {
      label: 'System Administrator',
      name: 'Operations Admin',
      email: 'admin@hospital.dev',
      pass: 'DevAdmin123!',
      role: 'ADMIN',
      badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
      activeBorder: 'border-amber-500 ring-2 ring-amber-100 bg-amber-50/40'
    },
  ];

  return (
    <div className="min-h-screen bg-[var(--pg-bg)] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Logo size="lg" showText={true} subtitle="Hospital Pharmacy Operations & Clinical Verification" />
        </div>

        <h2 className="mt-6 text-center text-lg font-semibold text-[var(--pg-text)]">
          Sign in to your account
        </h2>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg px-4 sm:px-0">
        <div className="bg-white border border-[var(--pg-border)] py-7 px-6 shadow-sm rounded-xl sm:px-8 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-100 rounded-md flex items-start gap-2 text-red-700 text-[13px]">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {selectedRole && (
            <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between text-[12px] text-blue-900">
              <span className="flex items-center gap-1.5 font-medium">
                <Check className="w-4 h-4 text-blue-600" />
                Credentials filled for <strong>{testAccounts.find(a => a.role === selectedRole)?.name}</strong>
              </span>
              <span className="text-[11px] text-blue-700 font-mono">Ready</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-[13px] font-medium text-[var(--pg-text)] mb-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--pg-text-muted)]">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setSelectedRole(null); }}
                  required
                  placeholder="name@hospital.dev"
                  className="block w-full pl-10 pr-3 py-2.5 bg-white border border-[var(--pg-border)] rounded-md text-[13px] text-[var(--pg-text)] placeholder-[var(--pg-text-muted)] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-[13px] font-medium text-[var(--pg-text)] mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--pg-text-muted)]">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setSelectedRole(null); }}
                  required
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-3 py-2.5 bg-white border border-[var(--pg-border)] rounded-md text-[13px] text-[var(--pg-text)] placeholder-[var(--pg-text-muted)] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 flex justify-center items-center gap-2 py-2.5 px-4 rounded-md text-[13px] font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {isSubmitting && !activeLoginRole ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* 1-Click Role Sign In Section */}
          <div className="pt-5 border-t border-[var(--pg-border-light)]">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-bold text-[var(--pg-text-muted)] uppercase tracking-wider">
                Instant Role Sign-In (1-Click Demo Access)
              </span>
              <span className="text-[11px] text-[var(--pg-text-muted)]">Click button to sign in directly</span>
            </div>

            <div className="space-y-2">
              {testAccounts.map((acct) => {
                const isLoggingInThis = isSubmitting && activeLoginRole === acct.role;
                const isSelected = selectedRole === acct.role;

                return (
                  <div
                    key={acct.role}
                    className={`p-3 rounded-lg border transition-all flex items-center justify-between gap-3 ${
                      isSelected ? acct.activeBorder : 'bg-slate-50/70 hover:bg-slate-100/70 border-[var(--pg-border-light)]'
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => handleSelectAccount(acct.email, acct.pass, acct.role)}
                      className="text-left flex-1 min-w-0"
                      title="Click to populate credentials"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-semibold text-[var(--pg-text)] truncate">{acct.label}</span>
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded border ${acct.badgeColor}`}>
                          {acct.role.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-[12px] text-[var(--pg-text-muted)] mt-0.5 truncate">
                        {acct.name} · <span className="font-mono text-[11px]">{acct.email}</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => handleDirectSignIn(acct.email, acct.pass, acct.role)}
                      className="px-3 py-1.5 rounded-md text-[12px] font-medium text-white bg-slate-900 hover:bg-blue-600 disabled:opacity-50 transition-colors flex items-center gap-1.5 shrink-0 shadow-sm"
                    >
                      {isLoggingInThis ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                          <span>Signing in...</span>
                        </>
                      ) : (
                        <>
                          <span>Sign in</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Demo Security & Guardrails Card */}
            <div className="mt-4 p-3.5 rounded-lg bg-slate-50 border border-[var(--pg-border)] space-y-2 text-[11px] text-[var(--pg-text-secondary)]">
              <div className="font-semibold text-[var(--pg-text)] flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-blue-600" />
                <span>Public Demo Safety & Architecture</span>
              </div>
              <ul className="space-y-1 text-[11px] list-disc list-inside text-[var(--pg-text-muted)]">
                <li><strong className="text-[var(--pg-text)]">Server-Side Credentials:</strong> Zero AWS keys in browser; Bedrock model calls execute exclusively server-side.</li>
                <li><strong className="text-[var(--pg-text)]">Rate Limiting & Quotas:</strong> Protected against automated abuse with per-session AI verification quotas.</li>
                <li><strong className="text-[var(--pg-text)]">Synthetic Records Only:</strong> Curated hospital compendium; entry of real PHI/PII is blocked.</li>
                <li><strong className="text-[var(--pg-text)]">Human-in-the-Loop:</strong> The AI agent acts in an advisory capacity; licensed human pharmacists retain dispensing authority.</li>
              </ul>
            </div>

            <p className="mt-4 text-center text-[11px] text-[var(--pg-text-muted)]">
              Hospital Pharmacy Operational Prototype. Test accounts are pre-configured.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
