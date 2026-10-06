"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  Lock,
  Mail,
  User,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, signup, loginWithGoogle } = useAuth();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successToast, setSuccessToast] = useState("");

  // Login Form States
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);

  // Signup Form States
  const [signupName, setSignupName] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");

  // Quick preset login helper
  const handleDemoLogin = async (name: string, email: string) => {
    setLoading(true);
    setErrorMessage("");
    const res = await signup(name, email, "Passcode123!");
    setLoading(false);
    if (res.success) {
      setSuccessToast(`Welcome, ${name}! Opening New Analysis...`);
      setTimeout(() => router.push("/"), 500);
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    setLoading(true);

    const res = await login(loginEmail, loginPassword);
    setLoading(false);

    if (res.success) {
      setSuccessToast("Verified! Opening New Analysis...");
      setTimeout(() => router.push("/"), 500);
    } else {
      setErrorMessage(res.error || "Authentication failed. Please check your credentials.");
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
    setLoading(true);

    const res = await signup(signupName, signupEmail, signupPassword);
    setLoading(false);

    if (res.success) {
      setSuccessToast(`Account authorized for ${signupName}! Opening New Analysis...`);
      setTimeout(() => router.push("/"), 500);
    } else {
      setErrorMessage(res.error || "Registration rejected.");
    }
  };

  const handleGoogleSignIn = async () => {
    setGoogleLoading(true);
    setErrorMessage("");
    const res = await loginWithGoogle();
    setGoogleLoading(false);

    if (res.success) {
      setSuccessToast("Google SSO Verified! Opening New Analysis...");
      setTimeout(() => router.push("/"), 500);
    } else {
      setErrorMessage(res.error || "Google authentication failed.");
    }
  };

  // Password strength calculator
  const getPasswordStrength = (pass: string) => {
    if (!pass) return { score: 0, text: "" };
    let score = 0;
    if (pass.length >= 6) score += 1;
    if (pass.length >= 10) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;

    if (score <= 1) return { score: 1, text: "Weak", color: "bg-red-500" };
    if (score <= 3) return { score: 2, text: "Moderate", color: "bg-amber-500" };
    return { score: 3, text: "Strong", color: "bg-emerald-500" };
  };

  const strength = getPasswordStrength(signupPassword);

  return (
    <div className="flex min-h-[calc(100vh-76px)] items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md space-y-6">

        {/* Main Card */}
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl transition dark:border-slate-800 dark:bg-[#111622] sm:p-8">

          {/* Header */}
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 shadow-lg shadow-blue-900/30">
              <svg viewBox="0 0 24 24" fill="none" className="h-6 w-6" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="9" stroke="white" strokeWidth="1.4" strokeOpacity="0.7" />
                <ellipse cx="12" cy="12" rx="4.5" ry="9" stroke="white" strokeWidth="1.4" strokeOpacity="0.7" />
                <line x1="3" y1="12" x2="21" y2="12" stroke="white" strokeWidth="1.4" strokeOpacity="0.7" />
                <circle cx="12" cy="12" r="1.8" fill="white" />
              </svg>
            </div>

            <h1 className="mt-4 text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              {mode === "login" ? "Account Sign In" : "Create New Account"}
            </h1>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {mode === "login"
                ? "Sign in with your email or Google account to continue."
                : "Create an account to start your geopolitical analysis."}
            </p>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="mt-6 grid grid-cols-2 gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-900">
            <button
              type="button"
              onClick={() => {
                setMode("login");
                setErrorMessage("");
              }}
              className={`rounded-lg py-1.5 text-xs font-semibold transition ${
                mode === "login"
                  ? "bg-white text-blue-600 shadow-sm dark:bg-slate-800 dark:text-blue-400"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              Sign In
            </button>

            <button
              type="button"
              onClick={() => {
                setMode("signup");
                setErrorMessage("");
              }}
              className={`rounded-lg py-1.5 text-xs font-semibold transition ${
                mode === "signup"
                  ? "bg-white text-blue-600 shadow-sm dark:bg-slate-800 dark:text-blue-400"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Toast / Error alerts */}
          {errorMessage && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successToast && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{successToast}</span>
            </div>
          )}

          {/* ONE-CLICK GOOGLE SIGN IN BUTTON */}
          <div className="mt-5">
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={googleLoading || loading}
              className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white py-2.5 px-4 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:border-slate-300 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              {googleLoading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
              ) : (
                <svg className="h-4 w-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
              )}
              <span>Continue with Google</span>
            </button>
          </div>

          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200 dark:border-slate-800" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase tracking-wider text-slate-400">
              <span className="bg-white px-2 dark:bg-[#111622]">Or with email</span>
            </div>
          </div>

          {/* FORM: Sign In */}
          {mode === "login" ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Email
                </label>
                <div className="relative mt-1">
                  <Mail className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="name@email.com"
                    className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-800 outline-none transition focus:border-blue-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setSuccessToast("Password reset link sent to your email.")}
                    className="text-[11px] font-medium text-blue-600 hover:underline dark:text-blue-400"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative mt-1">
                  <Lock className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-10 text-xs text-slate-800 outline-none transition focus:border-blue-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <label className="flex items-center gap-2 cursor-pointer text-slate-600 dark:text-slate-400">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Remember me</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-xs font-semibold text-white shadow-md transition hover:bg-blue-700 disabled:opacity-60"
              >
                {loading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <>
                    <span>Sign In & Start Analysis</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </>
                )}
              </button>
            </form>
          ) : (
            /* FORM: Sign Up / Register */
            <form onSubmit={handleSignupSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Full Name
                </label>
                <div className="relative mt-1">
                  <User className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={signupName}
                    onChange={(e) => setSignupName(e.target.value)}
                    placeholder="Shivangi Mohanty"
                    className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-800 outline-none transition focus:border-blue-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Email Address
                </label>
                <div className="relative mt-1">
                  <Mail className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    placeholder="name@email.com"
                    className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs text-slate-800 outline-none transition focus:border-blue-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Create Password
                </label>
                <div className="relative mt-1">
                  <Lock className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    placeholder="Minimum 6 characters"
                    className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-10 text-xs text-slate-800 outline-none transition focus:border-blue-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>

                {signupPassword && (
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                      <div
                        className={`h-full transition-all ${strength.color}`}
                        style={{ width: `${(strength.score / 3) * 100}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-medium text-slate-400">{strength.text}</span>
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-xs font-semibold text-white shadow-md transition hover:bg-blue-700 disabled:opacity-60"
              >
                {loading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <>
                    <span>Create Account & Start Analysis</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* Quick Preset One-Click Logins */}
          <div className="mt-6 border-t border-slate-100 pt-5 dark:border-slate-800">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 text-center mb-2.5">
              Quick One-Click Demo Login
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() =>
                  handleDemoLogin(
                    "Shivangi Mohanty",
                    "shivangi.mohanty@geointel.ai"
                  )
                }
                className="flex items-center justify-center rounded-xl border border-slate-100 bg-slate-50 py-2.5 px-3 text-center transition hover:border-blue-300 hover:bg-blue-50/60 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:bg-slate-800"
              >
                <span className="text-xs font-bold text-slate-800 dark:text-white">
                  Shivangi Mohanty
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  handleDemoLogin(
                    "Marcus Vance",
                    "m.vance@defense-intel.gov"
                  )
                }
                className="flex items-center justify-center rounded-xl border border-slate-100 bg-slate-50 py-2.5 px-3 text-center transition hover:border-blue-300 hover:bg-blue-50/60 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:bg-slate-800"
              >
                <span className="text-xs font-bold text-slate-800 dark:text-white">
                  Marcus Vance
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Back Link */}
        <div className="text-center">
          <Link
            href="/"
            className="text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
          >
            ← Back to New Analysis
          </Link>
        </div>

      </div>
    </div>
  );
}
