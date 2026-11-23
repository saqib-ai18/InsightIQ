import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '@/services/api'
import { useToast } from '@/hooks/useToast'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { success, error: toastError } = useToast()
  
  const from = (location.state as any)?.from?.pathname || '/overview'
  
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    if (!email) newErrors.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(email)) newErrors.email = 'Invalid email format'
    
    if (!isLogin) {
      if (!username) newErrors.username = 'Username is required'
      else if (username.length < 3) newErrors.username = 'Username must be at least 3 characters'
      
      if (!fullName) newErrors.fullName = 'Full name is required'
      
      if (!password) newErrors.password = 'Password is required'
      else if (password.length < 8) newErrors.password = 'Password must be at least 8 characters'
      
      if (password !== confirmPassword) newErrors.confirmPassword = 'Passwords do not match'
    } else {
      if (!password) newErrors.password = 'Password is required'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return
    
    setIsLoading(true)
    
    try {
      if (isLogin) {
        const response = await api.auth.login(email, password)
        localStorage.setItem('access_token', response.access_token)
        success('Welcome back!')
        navigate(from, { replace: true })
      } else {
        await api.auth.register(email, username, password, fullName)
        const loginResponse = await api.auth.login(email, password)
        localStorage.setItem('access_token', loginResponse.access_token)
        success('Account created successfully!')
        navigate(from, { replace: true })
      }
    } catch (err: any) {
      toastError(err.message || (isLogin ? 'Login failed' : 'Registration failed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 animate-in">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-xl bg-primary flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold text-text-primary">InsightIQ</h1>
          <p className="mt-2 text-text-secondary">
            {isLogin ? 'Sign in to your account' : 'Create a new account'}
          </p>
        </div>

        <div className="card">
          <div className="card-content p-6">
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              {!isLogin && (
                <div>
                  <label htmlFor="fullName" className="label">Full Name</label>
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className={`input ${errors.fullName ? 'border-error' : ''}`}
                    placeholder="John Doe"
                    autoComplete="name"
                    disabled={isLoading}
                  />
                  {errors.fullName && <p className="text-sm text-error mt-1">{errors.fullName}</p>}
                </div>
              )}
              
              {!isLogin && (
                <div>
                  <label htmlFor="username" className="label">Username</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <input
                      id="username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className={`input pl-10 ${errors.username ? 'border-error' : ''}`}
                      placeholder="johndoe"
                      autoComplete="username"
                      disabled={isLoading}
                    />
                  </div>
                  {errors.username && <p className="text-sm text-error mt-1">{errors.username}</p>}
                </div>
              )}

              <div>
                <label htmlFor="email" className="label">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`input pl-10 ${errors.email ? 'border-error' : ''}`}
                    placeholder="john@example.com"
                    autoComplete="email"
                    disabled={isLoading}
                  />
                </div>
                {errors.email && <p className="text-sm text-error mt-1">{errors.email}</p>}
              </div>

              <div>
                <label htmlFor="password" className="label">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`input pl-10 pr-10 ${errors.password ? 'border-error' : ''}`}
                    placeholder="••••••••"
                    autoComplete={isLogin ? 'current-password' : 'new-password'}
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-sm text-error mt-1">{errors.password}</p>}
              </div>

              {!isLogin && (
                <div>
                  <label htmlFor="confirmPassword" className="label">Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <input
                      id="confirmPassword"
                      type={showPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className={`input pl-10 ${errors.confirmPassword ? 'border-error' : ''}`}
                      placeholder="••••••••"
                      autoComplete="new-password"
                      disabled={isLoading}
                    />
                  </div>
                  {errors.confirmPassword && <p className="text-sm text-error mt-1">{errors.confirmPassword}</p>}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full py-3"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    {isLogin ? 'Signing in...' : 'Creating account...'}
                  </>
                ) : (
                  isLogin ? 'Sign In' : 'Create Account'
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-text-secondary">
                {isLogin ? "Don't have an account?" : 'Already have an account?'}
                <button
                  onClick={() => { setIsLogin(!isLogin); setErrors({}) }}
                  className="ml-2 text-primary hover:underline font-medium"
                >
                  {isLogin ? 'Sign up' : 'Sign in'}
                </button>
              </p>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-text-muted mt-6">
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  )
}

import { Sparkles } from 'lucide-react'